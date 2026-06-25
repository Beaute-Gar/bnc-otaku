"""
BNC-OTAKU — Bot Telegram Runner
Lance le bot Telegram en mode polling (développement local).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bots.telegram_handler import TelegramBotHandler


class SimpleManager:
    async def on_message_received(self, platform: str, sender: str, text: str):
        print(f"[{platform}] {sender}: {text}")


async def main():
    handler = TelegramBotHandler(SimpleManager())
    await handler.start()
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("BNC-Otaku Bot Telegram demarre (polling). Ctrl+C pour arreter.")
    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        await handler.stop()


if __name__ == "__main__":
    asyncio.run(main())
