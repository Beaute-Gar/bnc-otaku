from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Gemini ---
    gemini_api_key: str = ""

    # --- MySQL (legacy, prioritaire si DATABASE_URL non défini) ---
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "bnc_otaku_user"
    db_password: str = ""
    db_name: str = "bnc_otaku_db"
    db_ssl_ca: str = ""
    db_ssl_mode: str = "DISABLED"

    # --- PostgreSQL / DATABASE_URL (Render fournit DATABASE_URL auto) ---
    database_url: str = ""

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        url = f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        import os
        ca_path = self.db_ssl_ca.replace(chr(92), '/')
        if self.db_ssl_mode == "REQUIRED" and ca_path and os.path.isfile(ca_path):
            url += f"&ssl_ca={ca_path}"
        return url

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql") if self.database_url else False

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
