"""Script de lancement — python run.py ou python run.py --setup"""

import sys
import subprocess
import asyncio


def setup():
    print("📦 Installation des dépendances...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("🌐 Installation Chromium (Playwright)...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    print("\n✅ Terminé ! Copiez .env.example en .env, puis python run.py")


def run():
    from whatsapp_bot.main import main
    asyncio.run(main())


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup()
    else:
        run()
