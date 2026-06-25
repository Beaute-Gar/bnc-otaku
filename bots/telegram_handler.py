"""
Handler Telegram Bot
Utilise python-telegram-bot avec Webhook (mode production)
ou Polling (mode développement).
"""

import asyncio
import logging
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from backend.config import settings

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """Interface Telegram via python-telegram-bot."""

    def __init__(self, manager):
        self.manager = manager
        self.token = settings.telegram_bot_token
        self.webhook_url = settings.telegram_webhook_url
        self.app: Optional[Application] = None

    async def start(self):
        """Initialise et démarre le bot Telegram."""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN manquant")
            return

        self.app = Application.builder().token(self.token).build()

        # Commandes
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("examen", self._cmd_examen))
        self.app.add_handler(CommandHandler("certificat", self._cmd_certificat))
        self.app.add_handler(CommandHandler("aide", self._cmd_aide))

        # Messages texte
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

        # Démarrage
        if self.webhook_url:
            await self.app.bot.set_webhook(url=f"{self.webhook_url}/api/webhooks/telegram")
            logger.info(f"Telegram webhook configuré : {self.webhook_url}")
        else:
            await self.app.initialize()
            await self.app.start()
            # Polling
            asyncio.create_task(self._polling())
            logger.info("Telegram bot démarré en mode polling")

    async def _polling(self):
        """Boucle polling (dev)."""
        await self.app.updater.start_polling()

    async def stop(self):
        if self.app:
            await self.app.stop()
            await self.app.shutdown()

    async def send_message(self, chat_id: str, text: str):
        if self.app:
            await self.app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

    # --- Handlers ---

    def _site_url(self, path: str = "") -> str:
        url = settings.frontend_url.rstrip("/")
        return f"{url}{path}"

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎌 *Bienvenue au BNC-Otaku !*\n\n"
            "Je suis le bot officiel du Bureau National de Certification Otaku.\n\n"
            "Commandes :\n"
            "• `/examen` — Lancer l'examen de certification\n"
            "• `/certificat` — Vérifier un diplôme\n"
            "• `/aide` — Voir cette aide\n\n"
            f"Site officiel : {self._site_url()}",
            parse_mode="Markdown",
        )

    async def _cmd_examen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📜 *Examen National de Certification Otaku*\n\n"
            f"Rends-toi sur {self._site_url('/quiz.html')}\n\n"
            "10 questions genérées par IA Gemini avec 4 niveaux de difficulté !",
            parse_mode="Markdown",
        )

    async def _cmd_certificat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎓 *Vérification de Certificat*\n\n"
            f"Va sur {self._site_url()} et utilise la section "
            "'Vérifier un diplôme' avec ton numéro de certificat.",
            parse_mode="Markdown",
        )

    async def _cmd_aide(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._cmd_start(update, context)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback pour les messages texte non-commandes."""
        text = update.message.text
        sender = str(update.message.from_user.id)
        await self.manager.on_message_received("telegram", sender, text)
