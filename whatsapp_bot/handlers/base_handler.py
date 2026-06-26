"""Classe de base pour tous les handlers."""

from abc import ABC, abstractmethod
import logging

from whatsapp_bot.config import settings
from whatsapp_bot.services.database import DatabaseService

logger = logging.getLogger(__name__)


class BaseHandler(ABC):

    def __init__(self, db: DatabaseService):
        self.db = db

    @abstractmethod
    async def handle(self, message: dict) -> bool:
        ...

    async def send(self, message: dict, text: str) -> bool:
        logger.info(f"📤 Réponse vers {message.get('sender_name', 'inconnu')} : {text[:80]}...")
        return True

    def _contains_any(self, text: str, keywords: list) -> bool:
        return any(kw.lower() in text for kw in keywords)

    def _starts_with(self, text: str, commands: list) -> bool:
        return any(text.startswith(cmd.lower()) for cmd in commands)

    def _extract_arg(self, text: str, command: str) -> str:
        if text.lower().startswith(command.lower()):
            return text[len(command):].strip()
        return ""

    def _get_first_name(self, message: dict) -> str:
        name = message.get("sender_name", "")
        return name.split()[0] if name else "Otaku"
