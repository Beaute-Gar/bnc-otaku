"""/start, /info, /aide, /contact"""

from whatsapp_bot.handlers.base_handler import BaseHandler
from whatsapp_bot.config import settings


class InfoHandler(BaseHandler):

    COMMANDS_START = ["/start", "bonjour", "salut", "hello", "bonsoir"]
    COMMANDS_INFO = ["/info", "/presentation", "/bnc"]
    COMMANDS_AIDE = ["/aide", "/help", "/commandes", "/menu"]
    COMMANDS_CONTACT = ["/contact", "/email"]

    async def handle(self, message: dict) -> bool:
        text = message.get("text", "").lower().strip()
        if not text:
            return False

        if self._starts_with(text, self.COMMANDS_START):
            await self.send(message, self._response_start(message))
            return True
        if self._starts_with(text, self.COMMANDS_INFO):
            await self.send(message, self._response_info())
            return True
        if self._starts_with(text, self.COMMANDS_AIDE):
            await self.send(message, self._response_aide())
            return True
        if self._starts_with(text, self.COMMANDS_CONTACT):
            await self.send(message, self._response_contact())
            return True
        return False

    def _response_start(self, message: dict) -> str:
        name = self._get_first_name(message)
        return (
            f"🎌 *Bienvenue, {name} !*\n\n"
            "Agent officiel du *Bureau National de Certification Otaku*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎓 */quiz* — Passer l'examen\n"
            "🔍 */verifier [CODE]* — Vérifier un certificat\n"
            "📊 */classement* — Top 10 de la semaine\n"
            "🔗 */monlien* — Lien de parrainage\n"
            "📋 */info* — Présentation complète\n"
            "❓ */aide* — Toutes les commandes\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌐 {settings.SITE_URL}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _response_info(self) -> str:
        return (
            "🏛️ *BUREAU NATIONAL DE CERTIFICATION OTAKU*\n\n"
            "📌 *Mission :* Certifier les fans d'anime selon\n"
            "leur niveau de connaissance de la culture japonaise.\n\n"
            "🎯 *Comment ça marche :*\n"
            "1️⃣ Passez l'examen (10 questions)\n"
            "2️⃣ Obtenez votre grade (F → SS)\n"
            "3️⃣ Téléchargez votre diplôme PNG\n"
            "4️⃣ Partagez votre certification !\n\n"
            "🏆 *Grades :* F (Aspirant) → SS (Légendaire)\n\n"
            f"🌐 {settings.SITE_URL}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _response_aide(self) -> str:
        return (
            "❓ *Centre d'Aide BNC-Otaku*\n\n"
            "━━ *COMMANDES* ━━\n\n"
            "🎓 */quiz* — Passer l'examen\n"
            "🔍 */verifier CODE* — Vérifier un certificat\n"
            "📊 */classement* — Top 10 hebdomadaire\n"
            "🔗 */monlien* — Lien de parrainage\n"
            "👥 */parrains* — Stats de parrainage\n"
            "🏅 */mongrade* — Mon grade et mon score\n"
            "ℹ️ */info* — Présentation du BNC-Otaku\n"
            "📞 */contact* — Coordonnées\n\n"
            "🛠 *Problème de téléchargement ?*\n"
            "→ Autorisez les popups, attendez la pub 5s\n\n"
            "🔄 *Quiz ne charge pas ?*\n"
            "→ F5, videz le cache, réessayez"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _response_contact(self) -> str:
        return (
            "📞 *Djousse Tech Evolution — Contact*\n\n"
            f"🌐 {settings.SITE_URL}\n"
            "📧 contact@djousse.tech\n"
            "💬 Telegram : @BNCOtakuBot\n\n"
            "🕐 Lun-Ven 8h-20h, Sam 9h-15h (WAT)"
            f"{settings.OFFICIAL_FOOTER}"
        )
