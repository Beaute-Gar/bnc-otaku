from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api", tags=["contact"])


class ContactMessage(BaseModel):
    name: str
    email: str
    subject: str
    message: str


@router.post("/contact")
async def send_contact(msg: ContactMessage):
    if not msg.name or not msg.email or not msg.message:
        raise HTTPException(400, "Tous les champs obligatoires doivent être remplis")

    # Log en console (en attendant un service email)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"📬 NOUVEAU CONTACT\n"
        f"   Nom: {msg.name}\n"
        f"   Email: {msg.email}\n"
        f"   Sujet: {msg.subject}\n"
        f"   Message: {msg.message[:200]}"
    )

    return {"status": "ok", "detail": "Message reçu. Nous te répondrons sous 24-48h."}
