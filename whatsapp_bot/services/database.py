"""Service BDD asynchrone (reuse backend.database sync engine via threads)."""

import asyncio
import logging
from typing import Optional

from backend.database import session_factory

logger = logging.getLogger(__name__)


class DatabaseService:
    """Base de données du bot — utilise le même engine sync que le projet via run_in_executor."""

    def __init__(self):
        self._loop = asyncio.get_event_loop()

    async def connect(self):
        logger.info("DatabaseService prêt (reuse backend.database)")

    async def disconnect(self):
        logger.info("DatabaseService fermé")

    async def execute(self, query: str, params: dict = None) -> int:
        def _run():
            with session_factory() as db:
                result = db.execute(query, params or {})
                db.commit()
                return result.rowcount
        return await self._loop.run_in_executor(None, _run)

    async def fetch_one(self, query: str, params: dict = None) -> Optional[dict]:
        def _run():
            with session_factory() as db:
                from sqlalchemy import text
                result = db.execute(text(query), params or {}).fetchone()
                if result:
                    return dict(result._mapping)
                return None
        return await self._loop.run_in_executor(None, _run)

    async def fetch_all(self, query: str, params: dict = None) -> list[dict]:
        def _run():
            with session_factory() as db:
                from sqlalchemy import text
                result = db.execute(text(query), params or {}).fetchall()
                return [dict(r._mapping) for r in result]
        return await self._loop.run_in_executor(None, _run)

    async def execute_many(self, query: str, params_list: list[dict]) -> int:
        def _run():
            with session_factory() as db:
                total = 0
                for params in params_list:
                    total += db.execute(query, params).rowcount
                db.commit()
                return total
        return await self._loop.run_in_executor(None, _run)
