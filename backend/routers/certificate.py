from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.quiz import ExamSession
from backend.models.certificate import Certificate
from backend.security import get_current_user

router = APIRouter(prefix="/api/certificates", tags=["Certificats"])


class CertifyRequest(BaseModel):
    exam_session_id: int
    full_name: str


class CertifyResponse(BaseModel):
    cert_number: str
    full_name: str
    level: str
    score: int
    issued_at: str


class CertificateVerifyResponse(BaseModel):
    valid: bool
    cert_number: Optional[str] = None
    full_name: Optional[str] = None
    level: Optional[str] = None
    score: Optional[int] = None
    issued_at: Optional[str] = None


def _generate_cert_number() -> str:
    year = datetime.utcnow().year
    import random
    return f"BNC-{year}-{random.randint(1, 9999):04d}"


@router.post("/generate", response_model=CertifyResponse)
async def generate_certificate(
    req: CertifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExamSession).where(
            ExamSession.id == req.exam_session_id,
            ExamSession.user_id == user.id,
            ExamSession.status == "completed",
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou non terminée")

    result = await db.execute(
        select(Certificate).where(Certificate.exam_session_id == req.exam_session_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Certificat déjà généré pour cette session")

    cert_number = _generate_cert_number()

    cert = Certificate(
        user_id=user.id,
        exam_session_id=req.exam_session_id,
        cert_number=cert_number,
        full_name=req.full_name,
        level=session.level,
        score=session.score,
    )
    db.add(cert)
    await db.flush()
    await db.refresh(cert)

    return CertifyResponse(
        cert_number=cert.cert_number,
        full_name=cert.full_name,
        level=cert.level,
        score=cert.score,
        issued_at=cert.issued_at.isoformat() if cert.issued_at else "",
    )


@router.get("/verify/{cert_number}", response_model=CertificateVerifyResponse)
async def verify_certificate(cert_number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Certificate).where(Certificate.cert_number == cert_number)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        return CertificateVerifyResponse(valid=False, cert_number=cert_number)

    return CertificateVerifyResponse(
        valid=True,
        cert_number=cert.cert_number,
        full_name=cert.full_name,
        level=cert.level,
        score=cert.score,
        issued_at=cert.issued_at.isoformat() if cert.issued_at else None,
    )
