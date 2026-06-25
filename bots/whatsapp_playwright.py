"""
Handler WhatsApp via Playwright (WhatsApp Web).
Mode automatisé avec scan QR et détection de messages.
Réutilise l'architecture OTAKU_LOVE_PRO.
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser

from backend.config import settings

logger = logging.getLogger(__name__)


class WhatsAppPlaywrightHandler:
    """Bot WhatsApp via Playwright (WhatsApp Web)."""

    SELECTORS = {
        "qr_code": 'canvas[aria-label="Scan me!"]',
        "search_box": 'div[contenteditable="true"][data-tab="3"]',
        "message_input": 'div[contenteditable="true"][data-tab="10"]',
        "send_button": 'button[data-tab="11"]',
        "chat_list": "div._akbu",
        "last_message": "div.message-in span.selectable-text, div.message-out span.selectable-text",
    }

    def __init__(self, manager):
        self.manager = manager
        self.session_dir = Path(settings.whatsapp_session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.headless = settings.whatsapp_headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._running = False

    async def start(self):
        self._running = True
        logger.info("Démarrage WhatsApp Web (Playwright)...")

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await self.browser.new_context(
            user_data_dir=str(self.session_dir / "wa_session"),
            viewport={"width": 1280, "height": 720},
            locale="fr-FR",
        )

        self.page = await context.new_page()
        await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        # Attente QR ou authentification
        try:
            await self.page.wait_for_selector(self.SELECTORS["chat_list"], timeout=30000)
            logger.info("✅ WhatsApp Web déjà authentifié")
        except Exception:
            logger.info("📱 En attente du scan QR code WhatsApp...")
            try:
                await self.page.wait_for_selector("canvas[aria-label]", timeout=120000)
                logger.info("QR Code prêt, scanne avec WhatsApp")
                await self.page.wait_for_selector(self.SELECTORS["chat_list"], timeout=120000)
                logger.info("✅ WhatsApp Web authentifié !")
            except Exception as e:
                logger.error(f"❌ Échec authentification WhatsApp: {e}")
                return

        # Boucle d'écoute des messages
        asyncio.create_task(self._message_loop())

    async def _message_loop(self):
        """Boucle d'écoute des nouveaux messages."""
        last_count = 0
        while self._running:
            try:
                messages = await self.page.query_selector_all(self.SELECTORS["last_message"])
                if len(messages) > last_count:
                    for msg in messages[last_count:]:
                        text = await msg.inner_text()
                        # Traite le message via le manager central
                        await self.manager.on_message_received("whatsapp", "contact", text)
                    last_count = len(messages)
            except Exception as e:
                logger.debug(f"Erreur boucle messages: {e}")
            await asyncio.sleep(3)

    async def send_message(self, contact: str, text: str):
        """Envoie un message WhatsApp."""
        try:
            # Clique sur la recherche
            search = await self.page.query_selector(self.SELECTORS["search_box"])
            if search:
                await search.click()
                await search.fill(contact)
                await asyncio.sleep(1)
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(1)

            # Envoie le message
            msg_input = await self.page.query_selector(self.SELECTORS["message_input"])
            if msg_input:
                await msg_input.fill(text)
                await self.page.keyboard.press("Enter")
                logger.info(f"Message envoyé à {contact}")
        except Exception as e:
            logger.error(f"Erreur envoi WhatsApp: {e}")

    async def stop(self):
        self._running = False
        if self.browser:
            await self.browser.close()
