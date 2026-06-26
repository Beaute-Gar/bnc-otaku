"""
BNC-OTAKU WhatsApp Bot — Point d'entrée Render Worker.
Playwright headless + session persistée en BDD.

Premier déploiement :
  1. Lancer LOCALEMENT : python run_whatsapp.py
  2. Scanner le QR code
  3. La session est sauvegardée dans wa_sessions (BDD)
  4. Pusher sur GitHub → Render déploie et restore la session
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import session_factory
from whatsapp_bot.core.engine import WhatsAppEngine
from whatsapp_bot.core.dispatcher import MessageDispatcher
from whatsapp_bot.core.session_manager import SessionManager
from whatsapp_bot.services.database import DatabaseService
from whatsapp_bot.services.scheduler import BNCScheduler
from whatsapp_bot.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bnc_whatsapp")


async def main():
    logger.info("🎌 BNC-OTAKU WhatsApp Bot — Render Worker (headless)")

    db = DatabaseService()
    await db.connect()

    session_mgr = SessionManager(db)
    settings.SESSION_DIR = str(Path(__file__).resolve().parent / "sessions" / "whatsapp_session")

    engine = WhatsAppEngine(
        session_dir=settings.SESSION_DIR,
        headless=True,
        session_manager=session_mgr,
    )
    await engine.launch()

    connected = await engine.connect()
    if not connected:
        logger.error("❌ WhatsApp non connecté — session invalide ?")
        logger.error("   → Relance LOCALEMENT : python run_whatsapp.py")
        logger.error("   → Rescanne le QR, relance pour sauvegarder en BDD")
        logger.error("   → Re-push sur GitHub")
        await engine.close()
        await db.disconnect()
        return

    dispatcher = MessageDispatcher(db=db)
    scheduler = BNCScheduler(db=db)
    scheduler.start()

    logger.info("👂 WhatsApp Bot en écoute (headless)...")
    try:
        await engine.listen(callback=dispatcher.dispatch)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}", exc_info=True)
    finally:
        scheduler.stop()
        await engine.close()
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
