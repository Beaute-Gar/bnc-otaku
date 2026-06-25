import hmac
import hashlib
import json
import secrets
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import settings
from backend.models.payment import Payment, PremiumProduct


# --- Produits premium disponibles ---

DEFAULT_PRODUCTS = [
    {
        "slug": "diplome_gold",
        "name": "Diplôme Gold Edition",
        "description": "Diplôme premium avec cadre doré, sceau holographique et numéro unique",
        "prix_fcfa": 500,
        "badge_label": "Gold",
    },
    {
        "slug": "grade_boost",
        "name": "Grade Boost",
        "description": "Rehausse ton grade d'un niveau supérieur pendant 30 jours",
        "prix_fcfa": 200,
        "badge_label": "Boost",
    },
    {
        "slug": "pack_legendaire",
        "name": "Pack Légendaire",
        "description": "Diplôme Gold + Grade Boost + Badge Légendaire sur le classement",
        "prix_fcfa": 1000,
        "badge_label": "Légendaire",
    },
    {
        "slug": "ref_personnalise",
        "name": "Code Parrain Personnalisé",
        "description": "Choisis ton propre code de parrainage (ex: /ref TonPseudo)",
        "prix_fcfa": 300,
        "badge_label": "Custom",
    },
]


async def seed_products(db: AsyncSession):
    for prod in DEFAULT_PRODUCTS:
        result = await db.execute(select(PremiumProduct).where(PremiumProduct.slug == prod["slug"]))
        if not result.scalar_one_or_none():
            db.add(PremiumProduct(**prod))
    await db.flush()


def generate_reference() -> str:
    ts = datetime.utcnow().strftime("%y%m%d%H%M%S")
    rand = secrets.token_hex(3).upper()
    return f"BNC-{ts}-{rand}"


def generate_transaction_id() -> str:
    return f"TXN-{secrets.token_hex(8).upper()}"


class CinetPayService:
    """Intégration CinetPay pour les paiements Mobile Money (MTN/Orange)."""

    BASE_URL = "https://api.cinetpay.com/v1"

    def __init__(self):
        self.api_key = settings.cinetpay_api_key or ""
        self.site_id = settings.cinetpay_site_id or ""
        self.webhook_url = f"{settings.frontend_url}/api/payment/webhook"
        self.return_url = f"{settings.frontend_url}/premium.html?status=success"
        self.cancel_url = f"{settings.frontend_url}/premium.html?status=cancel"

    async def initiate_payment(
        self,
        montant_fcfa: int,
        operateur: str,
        phone: str,
        reference: str,
        description: str,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        import httpx

        payload = {
            "apikey": self.api_key,
            "site_id": self.site_id,
            "transaction_id": reference,
            "amount": montant_fcfa,
            "currency": "XAF",
            "description": description[:255],
            "customer_name": f"User_{user_id}" if user_id else "Anonyme",
            "customer_phone": phone,
            "notify_url": self.webhook_url,
            "return_url": self.return_url,
            "cancel_url": self.cancel_url,
            "channels": operateur.lower(),
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{self.BASE_URL}/payment", json=payload)
            data = resp.json()

        return data

    def verify_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        computed = hmac.new(
            self.api_key.encode(),
            json.dumps(payload, separators=(",", ":")).encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.site_id)


class NotchPayService:
    """Alternative NotchPay pour les paiements Mobile Money."""

    BASE_URL = "https://api.notchpay.co/v1"

    def __init__(self):
        self.public_key = settings.notchpay_public_key or ""

    async def initiate_payment(
        self, montant_fcfa: int, operateur: str, reference: str, description: str
    ) -> Dict[str, Any]:
        import httpx

        headers = {
            "Authorization": f"Bearer {self.public_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "amount": montant_fcfa,
            "currency": "XAF",
            "reference": reference,
            "description": description,
            "callback_url": f"{settings.frontend_url}/api/payment/webhook",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{self.BASE_URL}/charges", json=payload, headers=headers)
            data = resp.json()

        return data


cinetpay = CinetPayService()
notchpay = NotchPayService()
