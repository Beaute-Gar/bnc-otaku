"""Cerveau du bot — aiguillage des messages vers les handlers."""

import logging
from whatsapp_bot.config import settings
from whatsapp_bot.core.rate_limiter import RateLimiter
from whatsapp_bot.handlers.info_handler import InfoHandler
from whatsapp_bot.handlers.faq_handler import FAQHandler
from whatsapp_bot.handlers.certificate_handler import CertificateHandler
from whatsapp_bot.handlers.quiz_handler import QuizHandler
from whatsapp_bot.handlers.viral_handler import ViralHandler
from whatsapp_bot.handlers.referral_handler import ReferralHandler
from whatsapp_bot.services.database import DatabaseService

logger = logging.getLogger(__name__)


class MessageDispatcher:

    def __init__(self, db: DatabaseService):
        self.db = db
        self.rate_limiter = RateLimiter(
            max_per_contact=settings.MAX_MSGS_PER_CONTACT,
            window_seconds=86400
        )
        self.handlers = [
            InfoHandler(db),
            CertificateHandler(db),
            QuizHandler(db),
            ReferralHandler(db),
            ViralHandler(db),
            FAQHandler(db),
        ]
        logger.info(f"Dispatcher prêt — {len(self.handlers)} handlers")

    async def dispatch(self, message: dict):
        text = message.get("text", "").strip()
        has_image = message.get("has_image", False)
        if not text and not has_image:
            return

        sender_id = message.get("sender_id", "unknown")
        sender_name = message.get("sender_name", "Inconnu")
        is_group = message.get("is_group", False)

        logger.debug(f"📨 {sender_name} ({'groupe' if is_group else 'privé'}) : {text[:50]}...")

        if not self.rate_limiter.is_allowed(sender_id):
            logger.warning(f"⚠️ Rate limit : {sender_name} ignoré")
            return

        await self._log_interaction(message)

        for handler in self.handlers:
            try:
                if await handler.handle(message):
                    logger.debug(f"✅ Traité par {handler.__class__.__name__}")
                    return
            except Exception as e:
                logger.error(f"❌ Erreur {handler.__class__.__name__} : {e}", exc_info=True)

        if not is_group and text:
            logger.debug("🤷 Aucun handler — message ignoré")

    async def _log_interaction(self, message: dict):
        try:
            await self.db.execute(
                """INSERT INTO bot_wa_interactions (sender_id_hash, sender_name, message_type, is_group, created_at)
                   VALUES (SHA2(:sid, 256), :name, :type, :group, NOW())""",
                {
                    "sid": message.get("sender_id", ""),
                    "name": message.get("sender_name", ""),
                    "type": "image" if message.get("has_image") else "text",
                    "group": message.get("is_group", False),
                }
            )
        except Exception:
            pass
