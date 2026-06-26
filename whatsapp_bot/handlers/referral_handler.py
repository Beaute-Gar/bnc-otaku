"""Système de parrainage — /monlien, /parrains, /mongrade"""

import hashlib
import logging
from whatsapp_bot.handlers.base_handler import BaseHandler
from whatsapp_bot.config import settings

logger = logging.getLogger(__name__)


class ReferralHandler(BaseHandler):

    COMMANDS_LIEN = ["/monlien", "/lien", "/partager", "/ref"]
    COMMANDS_PARRAINS = ["/parrains", "/filleuls", "/stats"]
    COMMANDS_GRADE = ["/mongrade", "/monscore", "/moncertif"]

    async def handle(self, message: dict) -> bool:
        text = message.get("text", "").lower().strip()
        if not text:
            return False

        if self._starts_with(text, self.COMMANDS_LIEN):
            await self.send(message, await self._response_lien(message))
            return True
        if self._starts_with(text, self.COMMANDS_PARRAINS):
            await self.send(message, await self._response_parrains(message))
            return True
        if self._starts_with(text, self.COMMANDS_GRADE):
            await self.send(message, await self._response_grade(message))
            return True
        return False

    async def _response_lien(self, message: dict) -> str:
        sender_id = message.get("sender_id", "")
        sender_name = message.get("sender_name", "Otaku")
        first_name = self._get_first_name(message)

        ref_code = await self._get_or_create_ref_code(sender_id, sender_name)
        ref_link = f"{settings.REF_LINK_BASE}{ref_code}&utm_medium=wa_referral&utm_campaign=parrainage"

        share_text = (
            f"🎌 J'ai obtenu ma certification officielle Otaku !\n"
            f"Passe ton examen ici : {ref_link}"
        )

        return (
            f"🔗 *Votre lien de parrainage, {first_name} :*\n\n"
            f"`{ref_link}`\n\n"
            "📋 *Message à copier-coller :*\n"
            f"_{share_text}_\n\n"
            "📊 *Avantages :*\n"
            "• 3 filleuls → Badge Référent\n"
            "• 10 filleuls → Questions exclusives\n"
            "• 25 filleuls → Badge Maître\n"
            "• 50 filleuls → Diplôme Gold Edition"
            f"{settings.OFFICIAL_FOOTER}"
        )

    async def _response_parrains(self, message: dict) -> str:
        sender_id = message.get("sender_id", "")
        first_name = self._get_first_name(message)

        stats = await self._get_referral_stats(sender_id)
        if not stats:
            return (
                f"📊 *Stats parrainage, {first_name}*\n\n"
                "Aucun parrainage encore.\n"
                "Utilisez */monlien* pour commencer !"
                f"{settings.OFFICIAL_FOOTER}"
            )

        total = stats.get("total", 0)
        confirmed = stats.get("confirmed", 0)
        pending = total - confirmed
        niveau = self._get_niveau(confirmed)

        return (
            f"📊 *Stats de parrainage, {first_name}*\n\n"
            f"👥 Total : {total}\n"
            f"✅ Confirmés : {confirmed}\n"
            f"⏳ En attente : {pending}\n"
            f"🏅 Niveau : {niveau}\n\n"
            f"Prochain palier : {self._next_milestone(confirmed)}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    async def _response_grade(self, message: dict) -> str:
        sender_id = message.get("sender_id", "")
        first_name = self._get_first_name(message)

        cert = await self._get_best_certificate(sender_id)
        if not cert:
            return (
                f"📋 *Certification, {first_name}*\n\n"
                "Aucune certification trouvée.\n\n"
                f"👉 {settings.QUIZ_URL}"
                f"{settings.OFFICIAL_FOOTER}"
            )

        grade = cert.get("grade", "?")
        score = cert.get("score", "?")
        cert_number = cert.get("cert_number", "")
        date = cert.get("date_obtention", "")

        grade_labels = {
            "F": "⬜ Aspirant", "C": "🟫 Initié", "B": "⬛ Confirmé",
            "A": "🟡 Élite", "S": "🔵 Maître", "SS": "🔴 Légendaire"
        }
        grade_full = grade_labels.get(grade.upper(), f"Grade {grade}")

        return (
            f"🎓 *Certification de {first_name}*\n\n"
            f"📋 N° : `{cert_number}`\n"
            f"🏅 Grade : *{grade}* — {grade_full}\n"
            f"📊 Score : {score}/10\n"
            f"📅 Obtenu le : {date}\n\n"
            f"👉 {settings.QUIZ_URL}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    async def _get_or_create_ref_code(self, sender_id: str, sender_name: str) -> str:
        try:
            existing = await self.db.fetch_one(
                "SELECT ref_code FROM wa_users WHERE wa_id_hash = SHA2(:sid, 256) LIMIT 1",
                {"sid": sender_id}
            )
            if existing:
                return existing["ref_code"]

            ref_code = self._generate_ref_code(sender_id, sender_name)
            await self.db.execute(
                """INSERT INTO wa_users (wa_id_hash, display_name, ref_code, created_at)
                   VALUES (SHA2(:sid, 256), :name, :code, NOW())
                   ON DUPLICATE KEY UPDATE display_name = :name""",
                {"sid": sender_id, "name": sender_name[:50], "code": ref_code}
            )
            return ref_code
        except Exception as e:
            logger.error(f"Erreur création ref_code : {e}")
            return self._generate_ref_code(sender_id, sender_name)

    def _generate_ref_code(self, sender_id: str, sender_name: str) -> str:
        raw = f"{sender_id}_{sender_name}_{settings.SITE_URL}"
        h = hashlib.sha256(raw.encode()).hexdigest()[:8].upper()
        prefix = sender_name[:3].upper().replace(" ", "X") if sender_name else "WAU"
        return f"{prefix}{h}"

    async def _get_referral_stats(self, sender_id: str) -> dict | None:
        try:
            return await self.db.fetch_one(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN confirmed = 1 THEN 1 ELSE 0 END) as confirmed
                   FROM referrals r
                   JOIN wa_users u ON r.referrer_id = u.id
                   WHERE u.wa_id_hash = SHA2(:sid, 256)""",
                {"sid": sender_id}
            )
        except Exception:
            return None

    async def _get_best_certificate(self, sender_id: str) -> dict | None:
        try:
            return await self.db.fetch_one(
                """SELECT cert_number, grade, score,
                          DATE_FORMAT(created_at, '%%d/%%m/%%Y') as date_obtention
                   FROM certificates
                   WHERE sender_wa_id = :sid
                   ORDER BY score DESC, created_at DESC
                   LIMIT 1""",
                {"sid": sender_id}
            )
        except Exception:
            return None

    def _get_niveau(self, confirmed: int) -> str:
        if confirmed >= 50: return "🔴 Légendaire"
        if confirmed >= 25: return "🟡 Maître Parrain"
        if confirmed >= 10: return "⬛ Parrain Élite"
        if confirmed >= 3: return "🟫 Parrain Référent"
        return "⬜ Parrain Débutant"

    def _next_milestone(self, confirmed: int) -> str:
        milestones = [(3, "badge Référent"), (10, "quiz exclusifs"), (25, "badge Maître"), (50, "Diplôme Gold")]
        for target, reward in milestones:
            if confirmed < target:
                return f"→ *{target - confirmed} filleul(s)* de plus pour : _{reward}_"
        return "→ Niveau maximum atteint ! 🏆"
