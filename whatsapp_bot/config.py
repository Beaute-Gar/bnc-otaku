import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    SITE_URL: str = os.getenv("SITE_URL", "https://bnc-otaku.onrender.com")
    QUIZ_URL: str = f"{SITE_URL}/quiz.html"
    VERIFY_URL: str = f"{SITE_URL}/verify"
    PREMIUM_URL: str = f"{SITE_URL}/premium"

    BOT_NAME: str = "Agent BNC-Otaku"
    DIRECTOR_NAME: str = "BeauteGar"
    COMPANY_NAME: str = "Djousse Tech Evolution"

    OFFICIAL_FOOTER: str = (
        "\n\n─────────────────────\n"
        "🏛️ *Bureau National de Certification Otaku*\n"
        f"✅ Certifié par _{COMPANY_NAME}_\n"
        f"📋 Validé par *{DIRECTOR_NAME}*, Directeur\n"
        f"📄 Document émis par {COMPANY_NAME} — Validé par {DIRECTOR_NAME}, Directeur."
    )

    SESSION_DIR: str = os.getenv("SESSION_DIR", str(Path(__file__).resolve().parent / "sessions" / "whatsapp_session"))
    WHATSAPP_URL: str = "https://web.whatsapp.com"
    QR_TIMEOUT: int = 60
    CONNECTION_TIMEOUT: int = 30

    MIN_DELAY_BETWEEN_MSGS: float = 3.0
    MAX_DELAY_BETWEEN_MSGS: float = 8.0
    MAX_MSGS_PER_HOUR: int = 50
    MAX_MSGS_PER_CONTACT: int = 5
    COOLDOWN_AFTER_GROUP_MSG: float = 5.0

    LEADERBOARD_DAY: str = "sun"
    LEADERBOARD_HOUR: int = 20
    LEADERBOARD_MINUTE: int = 0
    DAILY_QUESTION_HOUR: int = 9
    DAILY_QUESTION_MINUTE: int = 0

    REF_LINK_BASE: str = f"{SITE_URL}/?ref="

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(Path(__file__).resolve().parent / "logs" / "bnc_bot.log"))

    KEYWORDS_DIPLOME: list = ["diplôme", "diplome", "certificat", "télécharger", "telecharger", "download"]
    KEYWORDS_PRIX: list = ["gratuit", "payant", "prix", "coût", "cout", "payer", "combien", "tarif"]
    KEYWORDS_AIDE: list = ["aide", "help", "comment", "bug", "problème", "probleme", "marche pas", "fonctionne pas", "erreur"]
    KEYWORDS_CONFIANCE: list = ["arnaque", "faux", "fiable", "vrai", "sécurisé", "securise", "danger", "hack", "virus"]
    KEYWORDS_QUIZ: list = ["quiz", "examen", "exam", "passer", "tester", "certification", "commencer", "start"]


settings = Settings()
