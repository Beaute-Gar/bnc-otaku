"""Moteur de croissance virale — détecte les partages de diplômes."""

import asyncio
import random
import hashlib
import logging
from whatsapp_bot.handlers.base_handler import BaseHandler
from whatsapp_bot.config import settings

logger = logging.getLogger(__name__)


class ViralHandler(BaseHandler):

    MIN_VIRAL_DELAY = 8.0
    MAX_VIRAL_DELAY = 20.0

    DIPLOME_CONTEXT_KEYWORDS = [
        "grade", "certif", "diplôme", "diplome", "score",
        "otaku", "bnc", "légendaire", "elite", "maître",
        "j'ai eu", "j'ai obtenu", "mon résultat"
    ]

    async def handle(self, message: dict) -> bool:
        has_image = message.get("has_image", False)
        is_group = message.get("is_group", False)
        text = message.get("text", "").lower()
        group_name = message.get("group_name", "groupe_inconnu")

        if not has_image:
            return False

        if not self._is_likely_diplome_share(text):
            return False

        logger.info(f"🎌 Partage détecté dans {'groupe ' + group_name if is_group else 'privé'}")

        delay = random.uniform(self.MIN_VIRAL_DELAY, self.MAX_VIRAL_DELAY)
        await asyncio.sleep(delay)

        viral_link = self._build_utm_link(
            source=self._hash_group_name(group_name) if is_group else "wa_direct",
            medium="whatsapp_sharing",
            campaign="diplome_viral",
        )

        sender_name = message.get("sender_name", "")
        grade_info = await self._get_sender_grade(message.get("sender_id", ""))
        response = self._response_viral(sender_name, grade_info.get("grade") if grade_info else None, viral_link, is_group)

        await self.send(message, response)
        await self._increment_share_count(message.get("sender_id", ""))
        return True

    def _is_likely_diplome_share(self, text: str) -> bool:
        if not text:
            return True
        return any(kw in text for kw in self.DIPLOME_CONTEXT_KEYWORDS)

    def _build_utm_link(self, source: str, medium: str, campaign: str) -> str:
        return f"{settings.SITE_URL}/?utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"

    def _hash_group_name(self, group_name: str) -> str:
        h = hashlib.md5(group_name.encode()).hexdigest()[:6]
        return f"wa_grp_{h}"

    async def _get_sender_grade(self, sender_id: str) -> dict | None:
        if not sender_id or sender_id == "unknown":
            return None
        try:
            return await self.db.fetch_one(
                "SELECT grade, score FROM certificates WHERE sender_wa_id = :sid LIMIT 1",
                {"sid": sender_id}
            )
        except Exception:
            return None

    async def _increment_share_count(self, sender_id: str):
        try:
            await self.db.execute(
                "UPDATE certificates SET share_count = share_count + 1 WHERE sender_wa_id = :sid",
                {"sid": sender_id}
            )
        except Exception:
            pass

    def _response_viral(self, sender_name: str, grade: str | None, link: str, is_group: bool) -> str:
        first_name = sender_name.split()[0] if sender_name else ""
        name_mention = f"*{first_name}*" if first_name else "ce candidat"
        intros = [
            f"🎌 Félicitations à {name_mention} !",
            f"🏆 Bravo à {name_mention} pour cette certification !",
            f"⭐ {name_mention} vient d'obtenir sa certification officielle !",
        ]
        intro = random.choice(intros)

        grade_text = ""
        if grade:
            grade_labels = {
                "F": "Aspirant Otaku", "C": "Otaku Initié", "B": "Otaku Confirmé",
                "A": "Otaku Élite", "S": "Otaku Maître", "SS": "Légendaire Otaku"
            }
            label = grade_labels.get(grade.upper(), f"Grade {grade}")
            grade_text = f"\nGrade obtenu : *{grade}* — _{label}_\n"

        cta = "Voulez-vous connaître votre propre grade officiel ?\n\n" if is_group else "Partagez votre certificat dans vos groupes !\n\n"

        return (
            f"{intro}\n{grade_text}\n"
            "Ce certificat est enregistré dans les archives\n"
            "officielles de Djousse Tech Evolution.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎓 {cta}"
            "Passez l'Examen National BNC-Otaku :\n"
            f"👉 {link}\n\n"
            "⏱️ _3 minutes • 10 questions • 100% gratuit_"
            f"{settings.OFFICIAL_FOOTER}"
        )
