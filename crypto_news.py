"""
crypto_news.py — CoinTelegraph RSS lentasidan eng so'nggi kripto yangiliklarini o'qiydi.

Muhim: bot birinchi marta ishga tushganda, RSS'dagi BARCHA (o'nlab eski) yangiliklarni
birdan yubormaydi — faqat "shu paytdan keyin chiqqan YANGI xabarlarni" belgilab, keyingi
tekshiruvlardan boshlab yuboradi. Bu "bootstrap" deb ataladi.
"""

import logging

import feedparser

from config import CRYPTO_NEWS_FEED_URL, CRYPTO_NEWS_MAX_PER_CYCLE

logger = logging.getLogger(__name__)

STATE_KEY = "crypto_news_seen_ids"
MAX_SEEN_IDS = 500  # xotira cheksiz kattalashib ketmasligi uchun


def fetch_news() -> list[dict] | None:
    """
    RSS lentasini o'qiydi va [{"id", "title", "link", "summary"}] ro'yxatini qaytaradi.
    Eng yangi xabar ro'yxat boshida bo'ladi. Xatolikda None qaytaradi.
    """
    try:
        parsed = feedparser.parse(CRYPTO_NEWS_FEED_URL)
    except Exception as exc:  # feedparser turli xil kutilmagan xatoliklarni chiqarishi mumkin
        logger.error("Kripto yangiliklar RSS'ni o'qib bo'lmadi: %s", exc)
        return None

    if parsed.bozo and not parsed.entries:
        logger.error("Kripto yangiliklar RSS formati noto'g'ri yoki bo'sh.")
        return None

    news = []
    for entry in parsed.entries:
        news.append(
            {
                "id": entry.get("id") or entry.get("link", ""),
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "").strip(),
            }
        )
    return news


def check_new_news(state: dict) -> list[dict]:
    """
    Yangi (hali ko'rilmagan) xabarlarni qaytaradi va state'ga "ko'rilgan" deb belgilaydi.
    Birinchi ishga tushishda (bootstrap) hech narsa qaytarmaydi, faqat hammasini "ko'rilgan"
    deb belgilab qo'yadi — shunda eski o'nlab xabar birdan spam bo'lib ketmaydi.
    """
    news = fetch_news()
    if news is None:
        return []

    seen_ids = state.get(STATE_KEY, [])
    seen_set = set(seen_ids)
    is_bootstrap = len(seen_ids) == 0

    # RSS eng yangidan boshlanadi, shuning uchun "eskisidan yangisiga" tartibda ko'ramiz
    candidates = [item for item in reversed(news) if item["id"] not in seen_set]

    new_items = [] if is_bootstrap else candidates[-CRYPTO_NEWS_MAX_PER_CYCLE:]

    for item in candidates:
        seen_ids.append(item["id"])

    state[STATE_KEY] = seen_ids[-MAX_SEEN_IDS:]

    if is_bootstrap and candidates:
        logger.info(
            "Kripto yangiliklar birinchi marta yuklandi (%s ta), hech narsa yuborilmadi (bootstrap).",
            len(candidates),
        )

    return new_items
