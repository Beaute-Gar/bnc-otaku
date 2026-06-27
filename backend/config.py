from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Gemini ---
    gemini_api_key: str = ""

    # --- Base de données ---
    database_url: str = ""

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        is_render = os.environ.get("RENDER") == "1"
        if is_render:
            return "sqlite:///data/bnc_otaku.db"
        return "sqlite:///bnc_otaku.db"

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql") if self.database_url else False

    @property
    def is_sqlite(self) -> bool:
        url = self.resolved_database_url
        return url.startswith("sqlite") if url else False

    # --- API Security ---
    api_secret_key: str = "change-me-pls"
    api_rate_limit: str = "100/minute"
    csrf_secret: str = "change-me-csrf"

    # --- Telegram ---
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""

    # --- Meta / WhatsApp Business ---
    meta_access_token: str = ""
    meta_phone_number_id: str = ""
    meta_webhook_verify_token: str = ""
    meta_webhook_url: str = ""

    # --- WhatsApp Playwright ---
    whatsapp_session_dir: str = "./wa_sessions"
    whatsapp_headless: bool = False

    # --- Admin ---
    admin_username: str = "admin"
    admin_password_hash: str = ""
    admin_email: str = "admin@bnc-otaku.cm"

    # --- CinetPay ---
    cinetpay_api_key: str = ""
    cinetpay_site_id: str = ""

    # --- NotchPay ---
    notchpay_public_key: str = ""

    # --- Frontend ---
    frontend_url: str = "https://bnc-otaku.onrender.com"
    cors_origins: str = "https://bnc-otaku.onrender.com"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
