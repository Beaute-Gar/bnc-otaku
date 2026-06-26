"""Planificateur — flash-question 9h, classement dimanche 20h, nettoyage 2h."""

import asyncio
import random
import json
import logging
from datetime import datetime

from whatsapp_bot.config import settings

logger = logging.getLogger(__name__)


class BNCScheduler:

    def __init__(self, db):
        self.db = db
        self._tasks = []
        self._running = False

    def start(self):
        self._running = True
        self._tasks = [
            asyncio.create_task(self._run_daily_question()),
            asyncio.create_task(self._run_weekly_leaderboard()),
            asyncio.create_task(self._run_cleanup()),
        ]
        logger.info(f"✅ Scheduler démarré — {len(self._tasks)} tâches")

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        logger.info("📅 Scheduler arrêté")

    async def _run_daily_question(self):
        while self._running:
            now = datetime.now()
            target = now.replace(hour=settings.DAILY_QUESTION_HOUR, minute=settings.DAILY_QUESTION_MINUTE, second=0)
            if now >= target:
                target = target.replace(day=target.day + 1)
            await asyncio.sleep((target - now).total_seconds())

            if not self._running:
                break
            await self._send_daily_question()

    async def _run_weekly_leaderboard(self):
        days_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        target_day = days_map.get(settings.LEADERBOARD_DAY, 6)

        while self._running:
            now = datetime.now()
            days_ahead = (target_day - now.weekday()) % 7
            target = now.replace(hour=settings.LEADERBOARD_HOUR, minute=settings.LEADERBOARD_MINUTE, second=0)
            target = target.replace(day=target.day + days_ahead)
            if days_ahead == 0 and now >= target:
                target = target.replace(day=target.day + 7)
            await asyncio.sleep((target - now).total_seconds())

            if not self._running:
                break
            await self._send_weekly_leaderboard()

    async def _run_cleanup(self):
        while self._running:
            now = datetime.now()
            target = now.replace(hour=2, minute=0, second=0)
            if now >= target:
                target = target.replace(day=target.day + 1)
            await asyncio.sleep((target - now).total_seconds())

            if not self._running:
                break
            await self._cleanup_old_data()

    async def _send_daily_question(self):
        logger.info("📨 Flash-question quotidienne...")
        try:
            question = await self.db.fetch_one(
                """SELECT question, options_json, reponse_correcte, categorie
                   FROM quiz_questions WHERE is_active = 1
                   ORDER BY RAND() LIMIT 1"""
            )
            if not question:
                logger.warning("⚠️ Aucune question disponible")
                return

            contacts = await self.db.fetch_all(
                """SELECT wa_id_hash, display_name FROM wa_users
                   WHERE last_interaction > DATE_SUB(NOW(), INTERVAL 30 DAY)
                     AND opt_out = 0 LIMIT 200"""
            )

            options = json.loads(question.get("options_json", "[]"))
            letters = ["A", "B", "C", "D"]
            opts = "\n".join(f"  {l}) {o}" for l, o in zip(letters, options[:4]))

            msg = (
                f"🎌 *FLASH-QUESTION DU JOUR — BNC-Otaku*\n"
                f"📂 {question.get('categorie', 'Anime')}\n\n"
                f"❓ *{question.get('question', '')}*\n\n{opts}\n\n"
                f"💡 Réponse sur le site ! 👉 {settings.SITE_URL}"
                f"{settings.OFFICIAL_FOOTER}"
            )

            for c in contacts:
                await asyncio.sleep(random.uniform(3.0, 8.0))
                logger.debug(f"→ Question à {c['display_name']}")

            logger.success(f"✅ Flash-question prête pour {len(contacts)} contacts")
        except Exception as e:
            logger.error(f"❌ Erreur flash-question : {e}", exc_info=True)

    async def _send_weekly_leaderboard(self):
        logger.info("📊 Classement hebdomadaire...")
        try:
            rows = await self.db.fetch_all(
                """SELECT firstname_used, grade, score,
                          DATE_FORMAT(created_at, '%%d/%%m') as date_exam
                   FROM certificates
                   WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                   ORDER BY score DESC, created_at ASC LIMIT 10"""
            )

            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            now = datetime.now()
            lines = [
                "━━━━━━━━━━━━━━━━━━━━━━━",
                f"🏆 *CLASSEMENT BNC-OTAKU*",
                f"📅 Semaine du {now.strftime('%d/%m/%Y')}",
                "━━━━━━━━━━━━━━━━━━━━━━━\n",
            ]
            if not rows:
                lines.append("Aucun score cette semaine.\nSoyez le premier !")
            else:
                for i, r in enumerate(rows):
                    lines.append(f"{medals[i]} *{r['firstname_used'][:12]}* — Grade *{r['grade']}* — {r['score']}/10")

            lines.append(f"\n👉 {settings.QUIZ_URL}")
            msg = "\n".join(lines) + settings.OFFICIAL_FOOTER

            contacts = await self.db.fetch_all(
                """SELECT wa_id_hash FROM wa_users
                   WHERE opt_out = 0 AND last_interaction > DATE_SUB(NOW(), INTERVAL 7 DAY)
                   LIMIT 300"""
            )
            logger.info(f"📤 Classement pour {len(contacts)} contacts")
            logger.success("✅ Classement hebdomadaire prêt")
        except Exception as e:
            logger.error(f"❌ Erreur classement : {e}")

    async def _cleanup_old_data(self):
        logger.info("🧹 Nettoyage...")
        try:
            deleted = await self.db.execute(
                "DELETE FROM bot_wa_interactions WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)"
            )
            logger.success(f"✅ {deleted} interactions supprimées")
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage : {e}")
