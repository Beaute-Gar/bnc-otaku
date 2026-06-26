"""Redirection vers l'examen et classement — /quiz, /classement"""

from whatsapp_bot.handlers.base_handler import BaseHandler
from whatsapp_bot.config import settings


class QuizHandler(BaseHandler):

    COMMANDS_QUIZ = ["/quiz", "/examen", "/exam", "/passer"]
    COMMANDS_CLASSEMENT = ["/classement", "/top", "/leaderboard", "/ranking"]

    async def handle(self, message: dict) -> bool:
        text = message.get("text", "").lower().strip()
        if not text:
            return False

        if self._starts_with(text, self.COMMANDS_QUIZ):
            await self.send(message, self._response_quiz(message))
            return True
        if self._starts_with(text, self.COMMANDS_CLASSEMENT):
            await self.send(message, await self._response_classement())
            return True
        return False

    def _response_quiz(self, message: dict) -> str:
        first_name = self._get_first_name(message)
        is_group = message.get("is_group", False)
        source = "wa_group" if is_group else "wa_private"
        link = f"{settings.QUIZ_URL}?utm_source={source}&utm_medium=whatsapp&utm_campaign=quiz_command"

        return (
            f"🎌 *Examen BNC-Otaku, {first_name} !*\n\n"
            "📋 10 questions de culture Anime\n"
            "🏆 Grade F → SS (Légendaire)\n"
            "📜 Diplôme PNG téléchargeable\n\n"
            f"👉 *Commencer :*\n{link}\n\n"
            "⏱️ 2-5 min • 🆓 Gratuit • 📝 Aucune inscription"
            f"{settings.OFFICIAL_FOOTER}"
        )

    async def _response_classement(self) -> str:
        try:
            rows = await self.db.fetch_all(
                """
                SELECT firstname_used, grade, score,
                       DATE_FORMAT(created_at, '%%d/%%m') as date_exam
                FROM certificates
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY score DESC, created_at ASC
                LIMIT 10
                """
            )
        except Exception:
            rows = []

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        if not rows:
            return (
                "📊 *Classement hebdomadaire BNC-Otaku*\n\n"
                "Aucun score cette semaine.\n\n"
                "Soyez le premier !\n"
                f"👉 {settings.QUIZ_URL}"
                f"{settings.OFFICIAL_FOOTER}"
            )

        lines = ["📊 *TOP 10 — CLASSEMENT HEBDOMADAIRE*\n"]
        for i, row in enumerate(rows):
            medal = medals[i]
            name = row.get("firstname_used", "Otaku")[:15]
            grade = row.get("grade", "?")
            score = row.get("score", 0)
            date = row.get("date_exam", "")
            lines.append(f"{medal} *{name}* — Grade *{grade}* — {score}/10 _(le {date})_")

        lines.append(
            f"\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 {settings.QUIZ_URL}"
        )
        return "\n".join(lines) + settings.OFFICIAL_FOOTER
