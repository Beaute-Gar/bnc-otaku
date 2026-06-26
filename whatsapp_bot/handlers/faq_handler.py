"""Réponses automatiques aux questions fréquentes (mots-clés)."""

import asyncio
import random
from whatsapp_bot.handlers.base_handler import BaseHandler
from whatsapp_bot.config import settings


class FAQHandler(BaseHandler):

    async def handle(self, message: dict) -> bool:
        text = message.get("text", "").lower()
        is_group = message.get("is_group", False)
        if not text:
            return False

        response = None
        if self._contains_any(text, settings.KEYWORDS_DIPLOME):
            response = self._faq_diplome(message)
        elif self._contains_any(text, settings.KEYWORDS_PRIX):
            response = self._faq_prix(message)
        elif self._contains_any(text, settings.KEYWORDS_AIDE):
            response = self._faq_aide(message)
        elif self._contains_any(text, settings.KEYWORDS_CONFIANCE):
            response = self._faq_confiance(message)
        elif self._contains_any(text, settings.KEYWORDS_QUIZ):
            response = self._faq_quiz(message)

        if response:
            if is_group:
                await asyncio.sleep(random.uniform(5.0, 12.0))
            await self.send(message, response)
            return True
        return False

    def _faq_diplome(self, message: dict) -> str:
        name = self._get_first_name(message)
        greeting = f"Bonjour *{name}* ! 👋\n\n" if name else "Bonjour ! 👋\n\n"
        return (
            f"{greeting}Pour obtenir votre *Diplôme Officiel BNC-Otaku* :\n\n"
            f"1️⃣ Accédez à l'examen : 👉 {settings.QUIZ_URL}\n\n"
            "2️⃣ Répondez aux *10 questions* de culture Anime\n\n"
            "3️⃣ Entrez votre *prénom* sur la page résultat\n\n"
            "4️⃣ Cliquez sur *« Télécharger mon Diplôme »*\n"
            "   _(Une courte publicité s'affiche avant)_\n\n"
            "⏱️ *Moins de 3 minutes — 100% gratuit*"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _faq_prix(self, message: dict) -> str:
        return (
            "✅ *La certification BNC-Otaku est 100% GRATUITE !*\n\n"
            "❌ Aucun compte, carte bancaire ou abonnement requis.\n\n"
            "Seule votre *passion pour les Animes* 🎌 compte !\n\n"
            f"👉 {settings.QUIZ_URL}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _faq_aide(self, message: dict) -> str:
        return (
            "🛠️ *Support Technique BNC-Otaku*\n\n"
            "🔴 *Diplôme ne se télécharge pas ?*\n"
            "   → Attendez la pub 5s, autorisez les popups\n\n"
            "🟡 *Quiz ne charge pas ?*\n"
            "   → F5 ou videz le cache navigateur\n\n"
            "🔵 *Mauvais nom sur le certificat ?*\n"
            "   → Modifiez le prénom dans le champ avant téléchargement\n\n"
            f"🌐 {settings.SITE_URL}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _faq_confiance(self, message: dict) -> str:
        return (
            "🔒 *BNC-Otaku — Transparence*\n\n"
            "✅ *Divertissement fictif* — Certifications humoristiques\n"
            "✅ *Aucune donnée sensible collectée*\n"
            "✅ *Gratuit garanti* — Service de base toujours gratuit\n"
            "✅ *Revenus publicitaires* — Pas de vos données\n\n"
            f"📋 {settings.SITE_URL}/mentions-legales"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _faq_quiz(self, message: dict) -> str:
        name = self._get_first_name(message)
        greeting = f"Prêt(e) *{name}* ? 💪\n\n" if name else "Prêt(e) ? 💪\n\n"
        return (
            f"🎌 {greeting}"
            "*L'Examen de Certification Otaku vous attend !*\n\n"
            "📋 10 questions • ⏱️ 3 min • 🏆 6 grades\n"
            "📜 Diplôme PNG téléchargeable\n\n"
            f"👉 *Commencer :*\n{settings.QUIZ_URL}"
            f"{settings.OFFICIAL_FOOTER}"
        )
