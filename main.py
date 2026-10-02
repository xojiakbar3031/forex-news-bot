"""
main.py — Botning boshqaruv markazi.

Ishlash mantig'i (har CHECK_INTERVAL_SECONDS soniyada takrorlanadi):
  1. ForexFactory'dan joriy haftalik voqealar ro'yxatini olib keladi (parser.py)
  2. Har bir voqea uchun:
       - Agar voqeaga 15 daqiqa qolgan bo'lsa va ogohlantirish hali yuborilmagan bo'lsa -> yuboradi
       - Agar voqeaga 5 daqiqa qolgan bo'lsa va ogohlantirish hali yuborilmagan bo'lsa -> yuboradi
       - Agar voqea vaqti allaqachon o'tgan va "actual" natija paydo bo'lgan bo'lsa -> natijani yuboradi
  3. Har bir yuborilgan xabar state.json fayliga "yozib qo'yiladi" — qayta yubormaslik uchun

Ishga tushirish:  python main.py
To'xtatish:       Ctrl+C
"""

import logging
import sys
import threading
import time
from datetime import datetime, timedelta

import pytz

# Windows konsoli ba'zan emoji (UTF-8) belgilarni chiqara olmaydi va dastur
# to'xtab qolishiga sabab bo'ladi. Shuni oldini olish uchun konsolni UTF-8'ga o'tkazamiz.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

from config import (
    CHECK_INTERVAL_SECONDS,
    CRYPTO_NEWS_CHECK_INTERVAL_SECONDS,
    CRYPTO_PRICE_CHECK_INTERVAL_SECONDS,
    LIVE_POLL_TIMEOUT_MINUTES,
    RATE_LIMIT_BACKOFF_SECONDS,
    REMINDER_MINUTES,
    TIMEZONE,
)
from crypto_news import check_new_news
from crypto_price import check_price_alerts
from parser import fetch_events
from messages import (
    build_actual_message,
    build_crypto_news_message,
    build_crypto_price_message,
    build_reminder_message,
)
from notifier import send_message
from state import get_event_state, load_state, save_state, set_event_flag
from web import start_web_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TASHKENT_TZ = pytz.timezone(TIMEZONE)


MAX_STATE_ENTRIES = 500


def _cleanup_old_state(state: dict) -> dict:
    """
    state.json cheksiz kattalashib ketmasligi uchun, faqat eng so'nggi
    MAX_STATE_ENTRIES ta voqea yozuvini saqlab qoladi.

    Eslatma: bu ataylab "hozirgi vaqt"ga bog'liq emas (masalan "3 kundan eski") —
    chunki ForexFactory lentasi ba'zan "shu hafta" nomi bilan bir necha kun oldingi
    voqealarni ham qaytaradi, va vaqtga asoslangan tozalash yangi yozilgan bayroqni
    o'sha zahotiyoq o'chirib yuborishi mumkin edi (bu xato aniqlanib, tuzatildi).
    """
    if len(state) <= MAX_STATE_ENTRIES:
        return state

    def _sort_key(event_id: str):
        try:
            return event_id.split("_", 1)[0]
        except (AttributeError, IndexError):
            return ""

    # Sana bo'yicha eng yangilaridan MAX_STATE_ENTRIES tasini saqlab qolamiz
    sorted_ids = sorted(state.keys(), key=_sort_key, reverse=True)
    keep_ids = set(sorted_ids[:MAX_STATE_ENTRIES])
    return {event_id: value for event_id, value in state.items() if event_id in keep_ids}


def process_event(event: dict, state: dict) -> None:
    """Bitta voqea uchun kerakli xabar yuborilishi kerak-emasligini tekshiradi va yuboradi."""
    event_id = event["event_id"]
    event_state = get_event_state(state, event_id)
    now = datetime.now(TASHKENT_TZ)
    minutes_until = (event["time_tashkent"] - now).total_seconds() / 60

    # --- 1. Ogohlantirishlar (15 va 5 daqiqa oldin) ---
    for minutes_before in REMINDER_MINUTES:
        flag_name = f"reminder_{minutes_before}_sent"
        already_sent = event_state.get(flag_name, False)

        if already_sent:
            continue

        # Voqeagacha shu chegaradan kam vaqt qolgan, lekin voqea hali o'tmagan bo'lsa
        if 0 < minutes_until <= minutes_before:
            text = build_reminder_message(event, minutes_before)
            if send_message(text):
                set_event_flag(state, event_id, flag_name)
                logger.info("Ogohlantirish yuborildi: '%s' (%s daqiqa qoldi)", event["title"], minutes_before)

    # --- 2. Natija (actual) e'lon qilinganda ---
    if not event_state.get("actual_sent", False):
        if minutes_until <= 0:
            if event["actual"]:
                text = build_actual_message(event)
                if send_message(text):
                    set_event_flag(state, event_id, "actual_sent")
                    logger.info("Natija yuborildi: '%s' -> %s", event["title"], event["actual"])
            elif minutes_until <= -LIVE_POLL_TIMEOUT_MINUTES:
                # Natija ko'p vaqt kutilsa ham chiqmadi — bekor qilamiz, cheksiz kutmaslik uchun
                set_event_flag(state, event_id, "actual_sent")
                logger.warning(
                    "'%s' uchun natija %s daqiqa ichida chiqmadi, kutish bekor qilindi.",
                    event["title"],
                    LIVE_POLL_TIMEOUT_MINUTES,
                )
            else:
                logger.info("'%s' natijasi hali chiqmagan, keyingi tekshiruvda qaraladi...", event["title"])


def process_crypto_prices(state: dict) -> None:
    """Kripto narxlarini tekshiradi, keskin o'zgarish bo'lsa kanalga yuboradi."""
    try:
        alerts = check_price_alerts(state)
    except Exception as exc:
        logger.exception("Kripto narxlarini tekshirishda kutilmagan xatolik: %s", exc)
        return

    for alert in alerts:
        text = build_crypto_price_message(alert)
        send_message(text)


def process_crypto_news(state: dict) -> None:
    """Yangi kripto yangiliklarini tekshiradi va kanalga yuboradi."""
    try:
        new_items = check_new_news(state)
    except Exception as exc:
        logger.exception("Kripto yangiliklarni tekshirishda kutilmagan xatolik: %s", exc)
        return

    for item in new_items:
        text = build_crypto_news_message(item)
        if send_message(text):
            logger.info("Kripto yangilik yuborildi: %s", item["title"])


def run_once(state: dict) -> tuple[dict, bool]:
    """
    Bitta tekshiruv aylanishini bajaradi: ma'lumot oladi, har bir voqeani qayta ishlaydi, saqlaydi.
    Ikkinchi qiymat sifatida "tarmoq xatosi bo'ldimi" (True/False) qaytaradi —
    shunga qarab main() qo'shimcha kutishi mumkin.
    """
    events = fetch_events()

    if events is None:
        logger.warning("Ma'lumot olinmadi (tarmoq xatosi). Keyingi urinish biroz kechroq bo'ladi.")
        return state, True

    logger.info("Tekshirildi: %s ta muhim USD voqea topildi.", len(events))

    for event in events:
        process_event(event, state)

    state = _cleanup_old_state(state)
    save_state(state)
    return state, False


def main() -> None:
    # "Uyg'otuvchi" mini-serverni fon oqimida (background thread) ishga tushiramiz —
    # bu asosiy botga (pastdagi while True tsikliga) hech qanday xalaqit bermaydi.
    threading.Thread(target=start_web_server, daemon=True).start()

    logger.info("Bot ishga tushdi. Har %s soniyada tekshiriladi.", CHECK_INTERVAL_SECONDS)
    state = load_state()

    # Kripto narx/yangilik tekshiruvlari forex tekshiruvidan kamroq tez-tez ishlaydi,
    # shuning uchun har birining "oxirgi marta qachon tekshirilgani" alohida kuzatiladi.
    last_crypto_price_check = 0.0
    last_crypto_news_check = 0.0

    while True:
        had_network_error = False
        try:
            state, had_network_error = run_once(state)

            now_mono = time.monotonic()
            if now_mono - last_crypto_price_check >= CRYPTO_PRICE_CHECK_INTERVAL_SECONDS:
                process_crypto_prices(state)
                last_crypto_price_check = now_mono
                save_state(state)

            if now_mono - last_crypto_news_check >= CRYPTO_NEWS_CHECK_INTERVAL_SECONDS:
                process_crypto_news(state)
                last_crypto_news_check = now_mono
                save_state(state)
        except Exception as exc:  # kutilmagan xatolik bot to'xtab qolishiga sabab bo'lmasin
            logger.exception("Kutilmagan xatolik yuz berdi: %s", exc)

        sleep_seconds = CHECK_INTERVAL_SECONDS + (RATE_LIMIT_BACKOFF_SECONDS if had_network_error else 0)
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C).")
