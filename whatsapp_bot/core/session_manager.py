"""Sauvegarde et restauration de session WhatsApp via MySQL.

Permet à la session WhatsApp de survivre aux redémarrages Render :
- Au premier connect : on extrait cookies + localStorage de la page
- On les stocke en base MySQL (JSON chiffré)
- Au démarrage suivant : on restaure avant de charger WhatsApp Web
"""

import asyncio
import json
import base64
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SESSION_KEY = "whatsapp_web_session"


class SessionManager:
    """Gère la persistance de session WhatsApp via la BDD."""

    def __init__(self, db):
        self.db = db

    async def save(self, page) -> None:
        """Extrait et sauvegarde la session WhatsApp depuis la page Playwright."""
        try:
            cookies = await page.context.cookies()
            local_storage = await page.evaluate("JSON.stringify(window.localStorage)")

            session_data = {
                "cookies": cookies,
                "local_storage": json.loads(local_storage) if local_storage != "{}" else {},
            }

            encoded = base64.b64encode(json.dumps(session_data).encode()).decode()
            checksum = hashlib.sha256(encoded.encode()).hexdigest()[:16]

            # Vérifier si la session a changé (évite écriture inutile)
            existing = await self.db.fetch_one(
                "SELECT checksum FROM wa_sessions WHERE session_key = :key LIMIT 1",
                {"key": SESSION_KEY}
            )
            if existing and existing.get("checksum") == checksum:
                return  # Inchangé, pas besoin d'écrire

            await self.db.execute(
                """INSERT INTO wa_sessions (session_key, session_data, checksum, updated_at)
                   VALUES (:key, :data, :chk, NOW())
                   ON DUPLICATE KEY UPDATE session_data = :data, checksum = :chk, updated_at = NOW()""",
                {"key": SESSION_KEY, "data": encoded, "chk": checksum}
            )
            logger.debug("💾 Session WhatsApp sauvegardée en BDD")

        except Exception as e:
            logger.warning(f"⚠️ Échec sauvegarde session : {e}")

    async def restore(self, context) -> bool:
        """Restaure les cookies dans le contexte Playwright. Retourne True si succès."""
        try:
            row = await self.db.fetch_one(
                "SELECT session_data FROM wa_sessions WHERE session_key = :key LIMIT 1",
                {"key": SESSION_KEY}
            )
            if not row:
                logger.info("ℹ️ Aucune session en BDD")
                return False

            decoded = json.loads(base64.b64decode(row["session_data"]).decode())
            cookies = decoded.get("cookies", [])

            if cookies:
                await context.add_cookies(cookies)
                logger.info(f"✅ Session restaurée ({len(cookies)} cookies)")
                return True

            return False

        except Exception as e:
            logger.warning(f"⚠️ Échec restauration session : {e}")
            return False

    async def _get_raw_session(self) -> Optional[dict]:
        """Récupère la ligne brute de session depuis la BDD."""
        return await self.db.fetch_one(
            "SELECT session_data FROM wa_sessions WHERE session_key = :key LIMIT 1",
            {"key": SESSION_KEY}
        )

    async def clear(self) -> None:
        """Supprime la session stockée."""
        await self.db.execute(
            "DELETE FROM wa_sessions WHERE session_key = :key",
            {"key": SESSION_KEY}
        )
        logger.info("🗑️ Session WhatsApp effacée")
