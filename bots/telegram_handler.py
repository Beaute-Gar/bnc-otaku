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
from backend.database import session_factory
from backend.models.user import User
from backend.models.quiz import ExamSession
from backend.models.certificate import Certificate
from sqlalchemy import func

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
        self.app.add_handler(CommandHandler("inscription", self._cmd_inscription))
        self.app.add_handler(CommandHandler("premium", self._cmd_premium))
        self.app.add_handler(CommandHandler("profil", self._cmd_profil))
        self.app.add_handler(CommandHandler("stats", self._cmd_stats))
        self.app.add_handler(CommandHandler("top", self._cmd_top))
        self.app.add_handler(CommandHandler("partager", self._cmd_partager))
        self.app.add_handler(CommandHandler("site", self._cmd_site))
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
            "*Commandes disponibles :*\n"
            "• `/examen` — Lancer l'examen de certification\n"
            "• `/profil` — Voir mon profil otaku\n"
            "• `/certificat` — Vérifier un diplôme\n"
            "• `/inscription` — Créer un compte\n"
            "• `/premium` — Voir les offres premium\n"
            "• `/stats` — Statistiques globales\n"
            "• `/top` — Meilleurs otakus\n"
            "• `/partager` — Gagner le niveau Légendaire\n"
            "• `/site` — Lien direct vers le site\n"
            "• `/aide` — Voir cette aide\n\n"
            f"🌐 *Site officiel :* [Clique ici]({self._site_url()})",
            parse_mode="Markdown",
        )

    async def _cmd_examen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📜 *Examen National de Certification Otaku*\n\n"
            f"Tu peux passer l'examen ici :\n"
            f"🔗 {self._site_url('/quiz.html')}\n\n"
            "10 questions générées par IA avec 4 niveaux (facile → légendaire).\n"
            "Tu dois être connecté pour commencer.",
            parse_mode="Markdown",
        )

    async def _cmd_certificat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎓 *Vérification de Certificat*\n\n"
            "Pour vérifier un diplôme, rends-toi sur le site :\n"
            f"🔗 {self._site_url()}\n\n"
            "Entre ton numéro de certificat dans la section "
            "'Vérifier un diplôme'.",
            parse_mode="Markdown",
        )

    async def _cmd_inscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📝 *Créer un compte BNC-Otaku*\n\n"
            f"Inscris-toi directement ici :\n"
            f"🔗 {self._site_url('/login.html')}\n\n"
            "Après inscription, tu pourras passer l'examen "
            "et obtenir ton certificat !",
            parse_mode="Markdown",
        )

    async def _cmd_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "⭐ *Offres Premium BNC-Otaku*\n\n"
            "Boost ton expérience avec nos offres :\n\n"
            "• *Diplôme Gold Edition* — 500 FCFA\n"
            "• *Grade Boost* — 200 FCFA\n"
            "• *Pack Légendaire* — 1000 FCFA\n"
            "• *Code Parrain* — 300 FCFA\n\n"
            f"🔗 {self._site_url('/premium.html')}\n\n"
            "Paiement Mobile Money (MTN/Orange).",
            parse_mode="Markdown",
        )

    async def _cmd_profil(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            await update.message.reply_text(
                "👤 *Mon Profil Otaku*\n\n"
                "Envoie `/profil ton_pseudo` pour voir ton profil.\n"
                "Exemple : `/profil naruto_fan`",
                parse_mode="Markdown",
            )
            return
        username = args[0]
        with session_factory() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                await update.message.reply_text(
                    f"❌ Aucun utilisateur trouvé avec le pseudo `{username}`",
                    parse_mode="Markdown",
                )
                return
            exams = db.query(ExamSession).filter(
                ExamSession.user_id == user.id,
                ExamSession.status == "completed",
            ).all()
            total_exams = len(exams)
            best = db.query(ExamSession).filter(
                ExamSession.user_id == user.id,
                ExamSession.status == "completed",
            ).order_by(ExamSession.score.desc()).first()
            best_level = best.level if best else "Aucun"
            certs = db.query(Certificate).filter(
                Certificate.user_id == user.id
            ).count()
        await update.message.reply_text(
            f"👤 *Mon Profil Otaku*\n\n"
            f"📛 *Nom :* {user.full_name or '-'}\n"
            f"🆔 *Pseudo :* `{user.username}`\n"
            f"🏆 *Meilleur niveau :* {best_level}\n"
            f"📊 *Examens passés :* {total_exams}\n"
            f"🎓 *Certificats :* {certs}\n"
            f"📅 *Membre depuis :* {user.created_at.strftime('%d/%m/%Y') if user.created_at else '-'}",
            parse_mode="Markdown",
        )

    async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with session_factory() as db:
            total_users = db.query(User).count()
            total_exams = db.query(ExamSession).filter(
                ExamSession.status == "completed"
            ).count()
            total_certs = db.query(Certificate).count()
            legendary = db.query(ExamSession).filter(
                ExamSession.level == "legendary"
            ).count()
        await update.message.reply_text(
            "📊 *Statistiques BNC-Otaku*\n\n"
            f"👥 *Utilisateurs inscrits :* {total_users}\n"
            f"📝 *Examens complétés :* {total_exams}\n"
            f"🎓 *Certificats délivrés :* {total_certs}\n"
            f"🏆 *Légendaires :* {legendary}\n\n"
            f"🌐 {self._site_url()}",
            parse_mode="Markdown",
        )

    async def _cmd_top(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with session_factory() as db:
            top = db.query(
                User.username, User.full_name, ExamSession.score, ExamSession.level
            ).join(ExamSession, User.id == ExamSession.user_id).filter(
                ExamSession.status == "completed"
            ).order_by(ExamSession.score.desc()).limit(10).all()
        if not top:
            await update.message.reply_text(
                "🏆 *Classement Otaku*\n\n"
                "Aucun examen complété pour le moment.\n"
                f"Sois le premier ! {self._site_url('/quiz.html')}",
                parse_mode="Markdown",
            )
            return
        lines = ["🏆 *Top 10 Meilleurs Otakus*\n"]
        for i, (uname, fname, score, level) in enumerate(top, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            name = fname or uname
            lines.append(f"{medal} *{name}* — {score}% ({level})")
        lines.append(f"\n🌐 {self._site_url()}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def _cmd_partager(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        site = self._site_url()
        msg = (
            "🎯 *Deviens un Otaku Légendaire !*\n\n"
            "Invite tes amis à passer l'examen BNC-Otaku.\n"
            "Plus vous êtes nombreux, plus tu gagnes en notoriété !\n\n"
            f"🔗 *Lien du site :* {site}\n"
            f"🤖 *Lien du bot :* https://t.me/BNC_Otaku_Bot\n\n"
            "Partage ce message avec tes amis et atteignez "
            "ensemble le niveau **Légendaire** ! 🏆"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def _cmd_site(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🌐 *BNC-Otaku — Site Officiel*\n\n"
            f"🔗 {self._site_url()}\n\n"
            "Retrouve toutes les fonctionnalités : "
            "examen, certificats, premium et classement.",
            parse_mode="Markdown",
        )

    async def _cmd_aide(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._cmd_start(update, context)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback pour les messages texte non-commandes."""
        text = update.message.text
        sender = str(update.message.from_user.id)
        await self.manager.on_message_received("telegram", sender, text)
