from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.payment import Payment, PremiumProduct
from backend.services.payment_service import (
    cinetpay,
    notchpay,
    generate_reference,
    generate_transaction_id,
    seed_products,
    DEFAULT_PRODUCTS,
)
from backend.security import get_current_user, limiter

router = APIRouter(prefix="/api/payment", tags=["Paiement"])


# --- Schémas ---

class InitiateRequest(BaseModel):
    produit_slug: str
    operateur: str = Field(..., pattern="^(MTN|ORANGE|WAVE|MOOV|AIRTEL)$")
    phone: str = Field(..., min_length=8, max_length=15)


class InitiateResponse(BaseModel):
    success: bool
    reference: str
    payment_url: Optional[str] = None
    message: str = ""


class PaymentStatusResponse(BaseModel):
    statut: str
    reference: str
    montant_fcfa: int
    produit: str
    created_at: str
    confirmed_at: Optional[str] = None


class ProductResponse(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    prix_fcfa: int
    badge_label: Optional[str] = None


# --- Routes ---

@router.get("/products", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.query(PremiumProduct).filter(PremiumProduct.is_active == 1).all()
    return [
        ProductResponse(
            slug=p.slug,
            name=p.name,
            description=p.description,
            prix_fcfa=p.prix_fcfa,
            badge_label=p.badge_label,
        )
        for p in products
    ]


@router.post("/initiate", response_model=InitiateResponse)
@limiter.limit("5/minute")
def initiate_payment(
    request: Request,
    req: InitiateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(PremiumProduct).filter(
        PremiumProduct.slug == req.produit_slug,
        PremiumProduct.is_active == 1,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    ref = generate_reference()
    payment = Payment(
        user_id=user.id,
        montant_fcfa=product.prix_fcfa,
        operateur=req.operateur,
        reference=ref,
        produit=product.slug,
        description=f"{product.name} - {product.description}",
        phone=req.phone,
        statut="pending",
    )
    db.add(payment)
    db.flush()

    if cinetpay.is_configured():
        try:
            result_cinetpay = cinetpay.initiate_payment(
                montant_fcfa=product.prix_fcfa,
                operateur=req.operateur,
                phone=req.phone,
                reference=ref,
                description=product.name,
                user_id=user.id,
            )
            payment.transaction_id = result_cinetpay.get("data", {}).get("transaction_id", ref)
            payment.raw_webhook = str(result_cinetpay)
            payment_url = result_cinetpay.get("data", {}).get("payment_url", "")
            return InitiateResponse(
                success=True,
                reference=ref,
                payment_url=payment_url,
                message="Paiement initié. Confirme sur ton téléphone.",
            )
        except Exception as e:
            return InitiateResponse(
                success=False,
                reference=ref,
                message=f"Erreur passerelle: {str(e)}",
            )

    return InitiateResponse(
        success=False,
        reference=ref,
        message="Passerelle de paiement non configurée.",
    )


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    ref = body.get("transaction_id") or body.get("reference") or ""

    payment = db.query(Payment).filter(Payment.reference == ref).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    status = body.get("status", "failed")
    if status in ("success", "completed", "ACCEPTED"):
        payment.statut = "success"
        payment.confirmed_at = datetime.utcnow()
    elif status in ("failed", "CANCELED", "REFUSED"):
        payment.statut = "failed"
    else:
        payment.statut = "pending"

    payment.raw_webhook = str(body)

    return {"message": "Webhook reçu", "statut": payment.statut}


@router.get("/status/{reference}", response_model=PaymentStatusResponse)
def payment_status(
    reference: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(
        Payment.reference == reference,
        Payment.user_id == user.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    return PaymentStatusResponse(
        statut=payment.statut,
        reference=payment.reference,
        montant_fcfa=payment.montant_fcfa,
        produit=payment.produit,
        created_at=payment.created_at.isoformat() if payment.created_at else "",
        confirmed_at=payment.confirmed_at.isoformat() if payment.confirmed_at else None,
    )


@router.get("/history")
def payment_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payments = db.query(Payment).filter(
        Payment.user_id == user.id
    ).order_by(Payment.created_at.desc()).limit(50).all()
    return [
        {
            "reference": p.reference,
            "montant_fcfa": p.montant_fcfa,
            "operateur": p.operateur,
            "produit": p.produit,
            "statut": p.statut,
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
        }
        for p in payments
    ]


@router.get("/admin/history")
def admin_payment_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé à l'administration")

    payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(100).all()

    from sqlalchemy import func as sa_func
    total_row = db.query(
        sa_func.coalesce(sa_func.sum(Payment.montant_fcfa).filter(Payment.statut == "success"), 0),
        sa_func.coalesce(sa_func.count(Payment.id).filter(Payment.statut == "success"), 0),
    ).first()
    total_montant = float(total_row[0])
    total_count = total_row[1]

    return {
        "total_fcfa": total_montant,
        "total_transactions": total_count,
        "payments": [
            {
                "reference": p.reference,
                "user_id": p.user_id,
                "montant_fcfa": p.montant_fcfa,
                "operateur": p.operateur,
                "produit": p.produit,
                "statut": p.statut,
                "phone": p.phone,
                "created_at": p.created_at.isoformat() if p.created_at else "",
                "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
            }
            for p in payments
        ],
    }
