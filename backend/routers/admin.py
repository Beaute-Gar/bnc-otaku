import json
import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from backend.database import get_db
from backend.models.user import User
from backend.models.quiz import ExamSession, QuizQuestion
from backend.models.admin import AdEvent, ReferralClick, CertificateRecord

router = APIRouter(prefix="/api/admin", tags=["Admin"])
logger = logging.getLogger(__name__)

ADMIN_KEY = "bnc-admin-2026"


def verify_key(key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Clé admin invalide")


# ─── Schémas ───

class DashboardOut(BaseModel):
    total_users: int
    active_today: int
    total_certificates: int
    total_ad_views: int
    total_ad_revenue: float
    total_telegram_clicks: int
    total_whatsapp_clicks: int
    pass_rate: float
    grade_distribution: dict
    recent_users: List[dict]


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    highest_unlocked: str
    completed_levels: str


class CertificateOut(BaseModel):
    id: int
    username: str
    level_name: str
    grade: str
    score: int
    serial_number: str
    created_at: str


# ─── Endpoints ───

@router.get("/dashboard")
def get_dashboard(key: str = "", db: Session = Depends(get_db)):
    verify_key(key)

    total_users = db.query(sa_func.count(User.id)).scalar() or 0
    today = datetime.utcnow().date()
    active_today = db.query(sa_func.count(ExamSession.id)).filter(
        sa_func.date(ExamSession.started_at) == today
    ).scalar() or 0

    total_certs = db.query(sa_func.count(CertificateRecord.id)).scalar() or 0
    total_ads = db.query(sa_func.count(AdEvent.id)).scalar() or 0
    total_rev = db.query(sa_func.coalesce(sa_func.sum(AdEvent.revenue), 0)).scalar() or 0.0

    tg_clicks = db.query(sa_func.count(ReferralClick.id)).filter(
        ReferralClick.platform == "telegram"
    ).scalar() or 0
    wa_clicks = db.query(sa_func.count(ReferralClick.id)).filter(
        ReferralClick.platform == "whatsapp"
    ).scalar() or 0

    total_exams = db.query(sa_func.count(ExamSession.id)).filter(
        ExamSession.status == "completed"
    ).scalar() or 0
    passed = db.query(sa_func.count(ExamSession.id)).filter(
        ExamSession.status == "completed",
        ExamSession.score >= 55
    ).scalar() or 0
    pass_rate = round((passed / total_exams * 100), 1) if total_exams > 0 else 0

    grades = {}
    for g in ["SS", "S", "A", "B"]:
        cnt = db.query(sa_func.count(ExamSession.id)).filter(
            ExamSession.status == "completed",
            ExamSession.level == g
        ).scalar() or 0
        grades[g] = cnt

    recent = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_users = [
        {
            "id": u.id, "username": u.username, "email": u.email,
            "highest_unlocked": getattr(u, "highest_unlocked", "Junior Otaku"),
            "completed_levels": getattr(u, "completed_levels", "[]"),
        }
        for u in recent
    ]

    return DashboardOut(
        total_users=total_users,
        active_today=active_today,
        total_certificates=total_certs,
        total_ad_views=total_ads,
        total_ad_revenue=round(total_rev, 2),
        total_telegram_clicks=tg_clicks,
        total_whatsapp_clicks=wa_clicks,
        pass_rate=pass_rate,
        grade_distribution=grades,
        recent_users=recent_users,
    )


@router.get("/users")
def list_users(key: str = "", db: Session = Depends(get_db)):
    verify_key(key)
    try:
        users = db.query(User).all()
        return [
            {
                "id": u.id, "username": u.username, "email": u.email, "role": u.role,
                "highest_unlocked": getattr(u, "highest_unlocked", "Junior Otaku"),
                "completed_levels": getattr(u, "completed_levels", "[]"),
            }
            for u in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{username}")
def delete_user(username: str, key: str = "", db: Session = Depends(get_db)):
    verify_key(key)
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        db.delete(user)
        return {"message": f"Utilisateur '{username}' supprimé"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/certificates")
def list_certificates(key: str = "", db: Session = Depends(get_db)):
    verify_key(key)
    certs = db.query(CertificateRecord).order_by(CertificateRecord.created_at.desc()).limit(50).all()
    return [
        CertificateOut(
            id=c.id, username=c.username, level_name=c.level_name,
            grade=c.grade, score=c.score, serial_number=c.serial_number,
            created_at=c.created_at.isoformat() if c.created_at else "",
        )
        for c in certs
    ]


@router.get("/questions")
def list_questions(key: str = ""):
    verify_key(key)
    from backend.routers.quiz import _ALL_QUESTIONS, LEVEL_ORDER
    return [
        {"index": i, "question": q["question"], "options": q["options"],
         "correct_index": q["correct_index"], "difficulty": q["difficulty"],
         "category": q.get("category", "")}
        for i, q in enumerate(_ALL_QUESTIONS)
    ]


@router.post("/ad/view")
def track_ad_view(request: Request, db: Session = Depends(get_db)):
    event = AdEvent(
        event_type="view",
        revenue=0.001,
        source="ad-gate",
        ip_address=request.client.host if request.client else None,
    )
    db.add(event)
    return {"status": "ok"}


@router.post("/referral/click")
def track_referral_click(
    platform: str = "",
    request: Request = None,
    db: Session = Depends(get_db),
):
    if platform not in ("telegram", "whatsapp"):
        raise HTTPException(status_code=400, detail="Plateforme invalide")
    click = ReferralClick(
        platform=platform,
        ip_address=request.client.host if request and request.client else None,
    )
    db.add(click)
    return {"status": "ok"}


@router.post("/certificate/generate")
def generate_certificate(
    username: str = "",
    level_name: str = "",
    grade: str = "",
    score: int = 0,
    db: Session = Depends(get_db),
):
    serial = f"BNC-{uuid.uuid4().hex[:12].upper()}"
    record = CertificateRecord(
        user_id=0,
        username=username or "Candidat",
        level_name=level_name,
        grade=grade,
        score=score,
        serial_number=serial,
    )
    db.add(record)
    return {"serial_number": serial, "message": "Certificat enregistré"}
