"""Moteur Playwright pour WhatsApp Web — connexion, écoute, envoi."""

import asyncio
import random
import logging
from pathlib import Path
from typing import Callable, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from whatsapp_bot.config import settings

logger = logging.getLogger(__name__)


class WhatsAppEngine:
    """Moteur WhatsApp Web via Playwright avec persistance session."""

    def __init__(self, session_dir: str, headless: bool = False, session_manager=None):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._headless = headless
        self._session_manager = session_manager
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._msg_count_this_hour = 0

    async def launch(self):
        self._playwright = await async_playwright().start()

        # Restaurer la session depuis la BDD avant de lancer Chrome
        if self._session_manager:
            temp_ctx = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_dir),
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            restored = await self._session_manager.restore(temp_ctx)
            await temp_ctx.close()
            if restored:
                logger.info("✅ Session restaurée depuis BDD")

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_dir),
            headless=self._headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()

        # Restaurer localStorage si présent
        if self._session_manager:
            try:
                row = await self._session_manager._get_raw_session()
                if row:
                    import json, base64
                    data = json.loads(base64.b64decode(row["session_data"]).decode())
                    ls = data.get("local_storage", {})
                    for key, val in ls.items():
                        try:
                            await self._page.evaluate(f"window.localStorage.setItem('{key}', '{val}')")
                        except Exception:
                            pass
                    logger.debug(f"localStorage restauré ({len(ls)} entrées)")
            except Exception:
                pass

    async def connect(self) -> bool:
        logger.info("📱 Ouverture WhatsApp Web...")
        await self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        try:
            qr_selector = 'canvas[aria-label="Scan this QR code to link a device"]'
            chat_selector = '[data-testid="chat-list"]'

            result = await self._page.wait_for_selector(
                f"{qr_selector}, {chat_selector}",
                timeout=settings.QR_TIMEOUT * 1000
            )

            el_id = await result.get_attribute("data-testid") if result else None

            if el_id == "chat-list":
                logger.success("✅ Session restaurée !")
                # Sauvegarder la session en BDD pour les prochains démarrages
                if self._session_manager:
                    await self._session_manager.save(self._page)
                return True
            else:
                logger.warning(f"📷 QR code affiché — scanne avec WhatsApp ({settings.QR_TIMEOUT}s)")
                await self._page.wait_for_selector(chat_selector, timeout=settings.QR_TIMEOUT * 1000)
                logger.success("✅ QR scanné — connecté !")
                # Sauvegarder la session après connexion
                if self._session_manager:
                    await self._session_manager.save(self._page)
                return True

        except Exception as e:
            if self._headless:
                # En mode headless : tenter la restauration BDD
                logger.warning(f"⚠️ Connexion headless échouée, tentative restauration BDD...")
            logger.error(f"❌ Connexion échouée : {e}")
            return False

    async def listen(self, callback: Callable):
        logger.info("👂 Écoute des messages...")

        await self._page.evaluate("""
            window._bnc_msgs = [];
            const obs = new MutationObserver((mutations) => {
                for (const m of mutations) {
                    for (const node of m.addedNodes) {
                        if (node.nodeType === 1 && node.classList.contains('message-in')) {
                            const el = node.querySelector('[data-pre-plain-text]');
                            if (el) {
                                const meta = el.getAttribute('data-pre-plain-text');
                                const txt = el.querySelector('.selectable-text span')?.innerText || '';
                                const img = !!node.querySelector('img.selectable-text');
                                window._bnc_msgs.push({meta, text: txt, has_image: img, ts: Date.now()});
                            }
                        }
                    }
                }
            });
            const chat = document.querySelector('#main') || document.body;
            obs.observe(chat, {childList: true, subtree: true});
        """)

        save_interval = 0
        while True:
            try:
                msgs = await self._page.evaluate("""
                    (() => { const m = [...window._bnc_msgs]; window._bnc_msgs = []; return m; })()
                """)
                for raw in msgs:
                    msg = self._parse_raw(raw)
                    if msg:
                        asyncio.create_task(callback(msg))

                # Sauvegarder la session toutes les ~5 minutes
                save_interval += 1
                if save_interval >= 150 and self._session_manager:
                    await self._session_manager.save(self._page)
                    save_interval = 0

            except Exception as e:
                logger.warning(f"⚠️ Boucle écoute : {e}")
            await asyncio.sleep(2)

    def _parse_raw(self, raw: dict) -> Optional[dict]:
        try:
            meta = raw.get("meta", "")
            return {
                "sender_id": "unknown",
                "sender_name": meta.split("]")[-1].strip().rstrip(":") if "]" in meta else "Inconnu",
                "text": raw.get("text", "").strip(),
                "is_group": ":" in meta and "@" not in meta,
                "group_name": None,
                "has_image": raw.get("has_image", False),
                "timestamp": raw.get("ts", 0),
            }
        except Exception:
            return None

    async def send_message(self, text: str) -> bool:
        try:
            await asyncio.sleep(random.uniform(
                settings.MIN_DELAY_BETWEEN_MSGS,
                settings.MAX_DELAY_BETWEEN_MSGS
            ))
            box = self._page.locator('[data-testid="conversation-compose-box-input"]')
            await box.click()
            await box.fill("")
            await box.type(text, delay=30)
            await box.press("Enter")
            self._msg_count_this_hour += 1
            logger.debug(f"📤 Message envoyé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur envoi : {e}")
            return False

    async def close(self):
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("🔒 Navigateur fermé")
