"""
BNC-OTAKU WHATSAPP BOT — v2.0
Djousse Tech Evolution — BeauteGar, Directeur
"""

import asyncio
import signal
import sys
import logging

from whatsapp_bot.core.engine import WhatsAppEngine
from whatsapp_bot.core.dispatcher import MessageDispatcher
from whatsapp_bot.services.database import DatabaseService
from whatsapp_bot.services.scheduler import BNCScheduler
from whatsapp_bot.config import settings

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bnc_bot")


async def main():
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║   BNC-OTAKU BOT — Démarrage...              ║")
    logger.info("╚══════════════════════════════════════════════╝")

    db = DatabaseService()
    await db.connect()

    engine = WhatsAppEngine(session_dir=settings.SESSION_DIR)
    await engine.launch()

    connected = await engine.connect()
    if not connected:
        logger.error("❌ Connexion WhatsApp échouée")
        await engine.close()
        sys.exit(1)

    dispatcher = MessageDispatcher(db=db)
    scheduler = BNCScheduler(db=db)
    scheduler.start()

    loop = asyncio.get_running_loop()

    def shutdown():
        logger.warning("⚠️ Arrêt...")
        asyncio.create_task(_shutdown(engine, scheduler, db))

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass  # Windows ne supporte pas add_signal_handler

    logger.info("🎌 Bot en écoute...")
    await engine.listen(callback=dispatcher.dispatch)


async def _shutdown(engine, scheduler, db):
    scheduler.stop()
    await engine.close()
    await db.disconnect()
    logger.info("👋 Au revoir !")
    sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt manuel.")
