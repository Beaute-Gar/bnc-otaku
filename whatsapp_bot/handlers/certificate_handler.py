"""Vérification de certificats — /verifier BNC-2025-XXXX"""

import re
import logging
from whatsapp_bot.handlers.base_handler import BaseHandler
from whatsapp_bot.config import settings

logger = logging.getLogger(__name__)


class CertificateHandler(BaseHandler):

    COMMANDS_VERIFY = ["/verifier", "/verify", "/check", "/valider"]
    CERT_PATTERN = re.compile(r'\bBNC-\d{4}-[A-Z0-9]{4,8}\b', re.IGNORECASE)

    async def handle(self, message: dict) -> bool:
        text = message.get("text", "").strip()
        text_lower = text.lower()
        if not text:
            return False

        cert_number = None

        if self._starts_with(text_lower, self.COMMANDS_VERIFY):
            for cmd in self.COMMANDS_VERIFY:
                cert_number = self._extract_arg(text, cmd)
                if cert_number:
                    break
            if not cert_number:
                await self.send(message, self._response_missing_code())
                return True
        else:
            match = self.CERT_PATTERN.search(text)
            if match:
                cert_number = match.group(0).upper()
            else:
                return False

        cert_data = await self._lookup_certificate(cert_number)
        if cert_data:
            await self.send(message, self._response_valid(cert_number, cert_data))
        else:
            await self.send(message, self._response_invalid(cert_number))
        return True

    async def _lookup_certificate(self, cert_number: str) -> dict | None:
        try:
            return await self.db.fetch_one(
                """
                SELECT cert_number, firstname_used, grade, score,
                       DATE_FORMAT(created_at, '%%d/%%m/%%Y') AS date_obtention,
                       share_count
                FROM certificates
                WHERE cert_number = :cert_number
                LIMIT 1
                """,
                {"cert_number": cert_number.upper()}
            )
        except Exception as e:
            logger.error(f"Erreur BDD certificat : {e}")
            return None

    def _response_valid(self, cert_number: str, data: dict) -> str:
        grade = data.get("grade", "?")
        firstname = data.get("firstname_used", "Candidat")
        score = data.get("score", "?")
        date_obtention = data.get("date_obtention", "inconnue")
        share_count = data.get("share_count", 0)

        grade_info = {
            "F": ("⬜", "Aspirant Otaku"), "C": ("🟫", "Otaku Initié"),
            "B": ("⬛", "Otaku Confirmé"), "A": ("🟡", "Otaku Élite"),
            "S": ("🔵", "Otaku Maître"), "SS": ("🔴", "Légendaire Otaku"),
        }
        emoji, titre = grade_info.get(grade.upper(), ("🏅", f"Grade {grade}"))

        return (
            "✅ *CERTIFICAT AUTHENTIQUE CONFIRMÉ*\n\n"
            f"📋 *N°* : `{cert_number}`\n"
            f"👤 *Titulaire* : {firstname}\n"
            f"{emoji} *Grade* : *{grade}* — _{titre}_\n"
            f"📊 *Score* : {score}/10\n"
            f"📅 *Date* : {date_obtention}\n"
            f"🔗 *Partagé* : {share_count} fois\n\n"
            "🏛️ _Certificat enregistré dans les archives officielles._\n\n"
            f"🌐 Vérifier en ligne : {settings.VERIFY_URL}/{cert_number}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _response_invalid(self, cert_number: str) -> str:
        return (
            "❌ *CERTIFICAT NON RECONNU*\n\n"
            f"Le numéro `{cert_number}` ne figure pas dans nos archives.\n\n"
            "Causes : numéro incorrect, certificat non généré ici,\n"
            "ou antérieur à notre système.\n\n"
            f"💡 Obtenez votre certificat : 👉 {settings.QUIZ_URL}"
            f"{settings.OFFICIAL_FOOTER}"
        )

    def _response_missing_code(self) -> str:
        return (
            "🔍 *Vérification de Certificat*\n\n"
            "Format : `/verifier BNC-2025-XXXXXX`\n\n"
            "Exemple :\n"
            "`/verifier BNC-2025-A3F9C2`\n\n"
            "Le numéro est inscrit en bas à gauche du diplôme."
            f"{settings.OFFICIAL_FOOTER}"
        )
