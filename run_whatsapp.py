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
        msg = text.lower().strip()

        if msg in ("bonjour", "hi", "salut", "hello"):
            reply = (
                "🎌 *Bienvenue au BNC-Otaku !*\n\n"
                "Commandes :\n"
                "• `examen` — Lien vers l'examen\n"
                "• `site` — Lien du site\n"
                "• `stats` — Statistiques\n\n"
                f"Site : https://bnc-otaku.onrender.com"
            )
        elif msg == "examen":
            reply = f"📜 Passe l'examen ici : https://bnc-otaku.onrender.com/quiz.html"
        elif msg == "site":
            reply = f"🌐 https://bnc-otaku.onrender.com"
        elif msg == "stats":
            from backend.database import session_factory
            from backend.models.user import User
            from backend.models.quiz import ExamSession
            with session_factory() as db:
                users = db.query(User).count()
                exams = db.query(ExamSession).filter(ExamSession.status == "completed").count()
            reply = f"📊 BNC-Otaku : {users} inscrits, {exams} examens complétés"
        else:
            reply = f"🤖 Commande inconnue. Envoie `bonjour` pour voir l'aide."

        await handler.send_message(sender, reply)


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
