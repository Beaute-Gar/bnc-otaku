"""
Handler WhatsApp Business API (Meta).
Communication via l'API officielle de Meta.
"""

import logging
import httpx
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

META_API_BASE = "https://graph.facebook.com/v21.0"


class WhatsAppMetaHandler:
    """WhatsApp Business API via Meta."""

    def __init__(self, manager):
        self.manager = manager
        self.access_token = settings.meta_access_token
        self.phone_number_id = settings.meta_phone_number_id
        self.client = httpx.AsyncClient(timeout=30.0)
        self._running = False

    async def start(self):
        self._running = True
        if not self.access_token or not self.phone_number_id:
            logger.error("Meta API non configurée (META_ACCESS_TOKEN ou META_PHONE_NUMBER_ID manquant)")
            return
        logger.info("WhatsApp Meta API prêt")

    async def stop(self):
        self._running = False
        await self.client.aclose()

    async def send_message(self, to: str, text: str):
        """Envoie un message texte via l'API Meta."""
        url = f"{META_API_BASE}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Message envoyé via Meta API à {to}: {data.get('messages', [{}])[0].get('id', 'N/A')}")
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur Meta API: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Erreur envoi Meta: {e}")

    async def handle_webhook(self, body: dict):
        """Traite un message entrant depuis le webhook Meta."""
        try:
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        sender = msg.get("from")
                        text = msg.get("text", {}).get("body", "")
                        if sender and text:
                            await self.manager.on_message_received("whatsapp", sender, text)
        except Exception as e:
            logger.error(f"Erreur traitement webhook Meta: {e}")
