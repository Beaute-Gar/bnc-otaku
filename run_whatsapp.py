"""
BNC-OTAKU — WhatsApp Bot v2.0 (modulaire)
Lance l'architecture professionnelle à 18 fichiers.

Premier lancement : scanne le QR code avec ton téléphone.
Usage :
  python run_whatsapp.py              → Démarre le bot
  python run_whatsapp.py --setup      → Installe les dépendances + Playwright
"""
import sys
import subprocess
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def setup():
    print("📦 Installation des dépendances...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(Path(__file__).parent / "whatsapp_bot" / "requirements.txt")], check=True)
    print("🌐 Installation Chromium (Playwright)...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    print("\n✅ Terminé ! Lance : python run_whatsapp.py")


def run():
    from whatsapp_bot.main import main
    asyncio.run(main())


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup()
    else:
        run()
