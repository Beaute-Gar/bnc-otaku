"""
Webhooks unifiés pour recevoir les messages de Telegram et WhatsApp.
Chaques messages entrants sont loggés dans bot_events pour traitement.
"""

from fastapi import APIRouter, Request, HTTPException
from backend.config import settings

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Reçoit les updates de Telegram Bot API.
    Nécessite TELEGRAM_BOT_TOKEN et TELEGRAM_WEBHOOK_URL configurés.
    """
    body = await request.json()
    # Log l'événement dans la DB (à implémenter)
    return {"ok": True}


@router.get("/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """
    Vérification du webhook Meta (hub.challenge).
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.meta_webhook_verify_token:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Échec vérification webhook")


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Reçoit les messages entrants de WhatsApp Business API.
    """
    body = await request.json()
    # Log l'événement dans la DB (à implémenter)
    return {"ok": True}
