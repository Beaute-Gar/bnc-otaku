"""
BNC-OTAKU — Bot WhatsApp (Playwright)
Lance WhatsApp Web en mode automatisé.
Premier lancement : scanne le QR code avec ton téléphone.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bots.whatsapp_playwright import WhatsAppPlaywrightHandler


class SimpleManager:
    async def on_message_received(self, platform: str, sender: str, text: str):
        print(f"[{platform}] {sender}: {text}")
        if text.lower() in ("bonjour", "hi", "salut"):
            from backend.database import session_factory
            from backend.models.user import User
            with session_factory() as db:
                count = db.query(User).count()
            await handler.send_message(
                sender,
                f"🎌 Bienvenue au BNC-Otaku !\n{count} otakus déjà inscrits.\nSite: https://bnc-otaku.onrender.com",
            )


async def main():
    global handler
    handler = WhatsAppPlaywrightHandler(SimpleManager())
    print("📱 Démarrage WhatsApp Web...")
    print("   ⚠️ Au premier lancement, scanne le QR code avec ton téléphone")
    print("   📸 Ouvre WhatsApp > Menu > Appareils liés > Scanner le code")
    await handler.start()
    print("✅ WhatsApp Bot en ligne !")
    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        await handler.stop()
        print("Bot WhatsApp arrêté.")


if __name__ == "__main__":
    asyncio.run(main())
