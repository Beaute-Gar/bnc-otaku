"""
Module 3 - Core du Bot Unifié (WhatsApp / Telegram)
====================================================
Point central qui écoute les événements entrants des deux plateformes,
détecte les certificats BNC-Otaku, et répond avec félicitations IA.
"""

import asyncio
import logging
from typing import Optional

from backend.config import settings
from backend.services.gemini_service import GeminiQuizGenerator

logger = logging.getLogger(__name__)


class UnifiedBotManager:
    """
    Gestionnaire unifié des bots.
    Délègue aux handlers spécifiques (Telegram / WhatsApp).
    """

    def __init__(self):
        self.telegram_bot: Optional["TelegramBotHandler"] = None
        self.whatsapp_playwright: Optional["WhatsAppPlaywrightHandler"] = None
        self.whatsapp_meta: Optional["WhatsAppMetaHandler"] = None
        self.gemini = GeminiQuizGenerator()
        self._running = False

    async def start(self):
        """Démarre tous les bots configurés."""
        self._running = True
        logger.info("🚀 Démarrage du système de bots unifié BNC-Otaku...")

        tasks = []

        # Démarrage Telegram
        if settings.telegram_bot_token:
            from bots.telegram_handler import TelegramBotHandler
            self.telegram_bot = TelegramBotHandler(self)
            tasks.append(self.telegram_bot.start())
            logger.info("✅ Bot Telegram configuré")
        else:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN non configuré")

        # Démarrage WhatsApp Playwright
        if settings.whatsapp_session_dir:
            from bots.whatsapp_playwright import WhatsAppPlaywrightHandler
            self.whatsapp_playwright = WhatsAppPlaywrightHandler(self)
            tasks.append(self.whatsapp_playwright.start())
            logger.info("✅ WhatsApp Playwright configuré")
        else:
            logger.warning("⚠️ WhatsApp Playwright non configuré (pas de session dir)")

        # Démarrage WhatsApp Meta API
        if settings.meta_access_token and settings.meta_phone_number_id:
            from bots.whatsapp_meta import WhatsAppMetaHandler
            self.whatsapp_meta = WhatsAppMetaHandler(self)
            tasks.append(self.whatsapp_meta.start())
            logger.info("✅ WhatsApp Meta API configuré")
        else:
            logger.warning("⚠️ WhatsApp Meta API non configuré")

        if tasks:
            await asyncio.gather(*tasks)

    async def stop(self):
        """Arrête tous les bots."""
        self._running = False
        if self.telegram_bot:
            await self.telegram_bot.stop()
        if self.whatsapp_playwright:
            await self.whatsapp_playwright.stop()
        if self.whatsapp_meta:
            await self.whatsapp_meta.stop()
        logger.info("🛑 Système de bots arrêté")

    async def on_message_received(self, platform: str, sender: str, message: str, metadata: dict = None):
        """
        Callback principal : traite un message entrant.
        Détecte les certificats BNC et répond avec l'IA.
        """
        logger.info(f"📩 [{platform}] Message de {sender}: {message[:100]}...")

        # Détection de certificat BNC-Otaku
        if "BNC-" in message.upper() or "certificat" in message.lower():
            await self._handle_certificate_check(platform, sender, message)

        # Détection de demande d'examen
        elif any(kw in message.lower() for kw in ["examen", "quiz", "test", "certification"]):
            await self._handle_exam_request(platform, sender, message)

        # Réponse générique IA
        else:
            await self._handle_generic(platform, sender, message)

    async def _handle_certificate_check(self, platform: str, sender: str, message: str):
        """Vérification de certificat BNC."""
        response = (
            "🎓 *Bureau National de Certification Otaku*\n\n"
            "Tu souhaites vérifier un certificat BNC ? "
            "Rends-toi sur https://bnc-otaku.cm/#verification "
            "et entre ton numéro de certificat.\n\n"
            "Ou passe l'examen si tu n'es pas encore certifié ! ✨"
        )
        await self._send_message(platform, sender, response)

    async def _handle_exam_request(self, platform: str, sender: str, message: str):
        """Demande d'examen."""
        response = (
            "📜 *Examen National de Certification Otaku*\n\n"
            "Prêt à prouver ta culture anime ? 🎌\n\n"
            "👉 Rends-toi sur https://bnc-otaku.cm/quiz.html\n"
            "10 questions générées par l'IA Gemini !\n\n"
            "Bonne chance, otaku-san ! ✨"
        )
        await self._send_message(platform, sender, response)

    async def _handle_generic(self, platform: str, sender: str, message: str):
        """Réponse générique avec l'IA Gemini."""
        try:
            congrat = self.gemini.generate_congratulation(sender, "fan", 0)
            response = f"🤖 BNC-Otaku Bot\n\n{congrat}\n\nPasse l'examen sur https://bnc-otaku.cm"
        except Exception:
            response = (
                "🤖 *BNC-Otaku Bot*\n\n"
                "Bienvenue ! Je suis le bot officiel du Bureau National de Certification Otaku.\n\n"
                "Commandes :\n"
                "• `examen` — Lancer l'examen de certification\n"
                "• `certificat` — Vérifier un diplôme\n"
                "• `quiz` — Générer un quiz aléatoire\n\n"
                "Site : https://bnc-otaku.cm"
            )
        await self._send_message(platform, sender, response)

    async def _send_message(self, platform: str, recipient: str, text: str):
        """Envoie un message sur la plateforme appropriée."""
        if platform == "telegram" and self.telegram_bot:
            await self.telegram_bot.send_message(recipient, text)
        elif platform == "whatsapp" and self.whatsapp_meta:
            await self.whatsapp_meta.send_message(recipient, text)
        elif platform == "whatsapp" and self.whatsapp_playwright:
            await self.whatsapp_playwright.send_message(recipient, text)
        else:
            logger.warning(f"Impossible d'envoyer sur {platform} : aucun handler actif")

    @property
    def is_running(self) -> bool:
        return self._running
