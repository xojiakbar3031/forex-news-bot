"""
notifier.py — Telegram kanalga xabar yuborish uchun javobgar modul.
Tarmoqda vaqtinchalik uzilish bo'lsa ham, 3 marta qayta urinib ko'radi.
"""

import asyncio
import logging
import time

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import BOT_TOKEN, CHANNEL_ID

logger = logging.getLogger(__name__)

_bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


async def _send_async(text: str) -> None:
    await _bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def send_message(text: str) -> bool:
    """
    Xabarni Telegram kanalga yuboradi. Muvaffaqiyatli bo'lsa True, aks holda False qaytaradi.
    Bot sozlanmagan bo'lsa (token/kanal yo'q bo'lsa), xabarni konsolga chiqarib qo'yadi —
    shunda dasturni sozlamalarsiz ham sinab ko'rish mumkin.
    """
    if _bot is None or not CHANNEL_ID:
        logger.warning("BOT_TOKEN yoki CHANNEL_ID sozlanmagan. Xabar faqat konsolga chiqarildi:")
        print("\n----- [TELEGRAM XABARI YUBORILMADI, TEST REJIMI] -----")
        print(text)
        print("--------------------------------------------------------\n")
        return False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            asyncio.run(_send_async(text))
            logger.info("Xabar muvaffaqiyatli yuborildi.")
            return True
        except TelegramError as exc:
            logger.error("Telegramga yuborishda xatolik (urinish %s/%s): %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    logger.error("Xabarni %s marta urinishdan keyin ham yuborib bo'lmadi.", MAX_RETRIES)
    return False
