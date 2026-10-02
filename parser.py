"""
parser.py — ForexFactory ochiq JSON lentasidan iqtisodiy voqealarni yuklab oladi
va faqat bizga kerakli (USD, High impact) voqealarni filtrlab qaytaradi.
"""

import logging
from datetime import datetime

import requests
import pytz

from config import CALENDAR_URL, TARGET_CURRENCY, TARGET_IMPACT, TIMEZONE

logger = logging.getLogger(__name__)

# Faqat shu nomdagi voqealar bilan ishlaymiz (topshiriqda ko'rsatilganlar)
RELEVANT_KEYWORDS = [
    "CPI",
    "Core CPI",
    "Non-Farm",
    "Nonfarm",
    "NFP",
    "Unemployment Rate",
    "FOMC",
    "GDP",
    "PPI",
    "Fed Interest Rate",
    "Federal Funds Rate",
]

TASHKENT_TZ = pytz.timezone(TIMEZONE)


def _is_relevant(title: str) -> bool:
    """Voqea nomi bizga kerakli kalit so'zlardan birini o'z ichiga oladimi?"""
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in RELEVANT_KEYWORDS)


def _parse_event_time(raw_date: str) -> datetime:
    """
    JSON'dagi vaqtni (masalan "2026-08-17T08:30:00-04:00") Toshkent vaqtiga o'giradi.
    """
    dt_utc_aware = datetime.fromisoformat(raw_date)
    return dt_utc_aware.astimezone(TASHKENT_TZ)


def fetch_events() -> list[dict] | None:
    """
    ForexFactory lentasidan barcha voqealarni yuklab oladi,
    faqat USD + High impact + bizga kerakli voqealarni qaytaradi.

    Har bir voqea quyidagi shaklda qaytariladi:
    {
        "event_id": "2026-08-17_CPI m/m",
        "title": "CPI m/m",
        "country": "USD",
        "impact": "High",
        "time_tashkent": datetime(...),
        "forecast": "0.3%",
        "previous": "0.2%",
        "actual": "0.4%" yoki "" (hali chiqmagan bo'lsa)
    }
    """
    try:
        response = requests.get(
            CALENDAR_URL,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (forex-news-bot/1.0)"},
        )
        response.raise_for_status()
        raw_events = response.json()
    except requests.RequestException as exc:
        logger.error("Kalendarni yuklab bo'lmadi: %s", exc)
        return None  # None = "tarmoq xatosi", [] = "muvaffaqiyatli, lekin mos voqea yo'q"
    except ValueError as exc:
        logger.error("Kalendar JSON formatini o'qib bo'lmadi: %s", exc)
        return None

    events = []
    for item in raw_events:
        try:
            if item.get("country") != TARGET_CURRENCY:
                continue
            if item.get("impact") != TARGET_IMPACT:
                continue
            title = item.get("title", "")
            if not _is_relevant(title):
                continue

            time_tashkent = _parse_event_time(item["date"])
            event_id = f"{time_tashkent.date().isoformat()}_{title}"

            events.append(
                {
                    "event_id": event_id,
                    "title": title,
                    "country": item.get("country", ""),
                    "impact": item.get("impact", ""),
                    "time_tashkent": time_tashkent,
                    "forecast": item.get("forecast", "") or "",
                    "previous": item.get("previous", "") or "",
                    "actual": item.get("actual", "") or "",
                }
            )
        except (KeyError, ValueError) as exc:
            logger.warning("Voqeani o'qishda xatolik, o'tkazib yuborildi: %s (%s)", item, exc)
            continue

    return events
