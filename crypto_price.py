"""
crypto_price.py — CoinGecko (bepul, kalitsiz API) orqali asosiy kriptovalyutalar
narxini kuzatadi. Agar 24 soatlik o'zgarish belgilangan chegaradan (masalan 5%)
katta bo'lsa, ogohlantirish xabari tayyorlaydi.

Bir xil coin uchun xabar spam bo'lib ketmasligi uchun "cooldown" (kutish vaqti)
qo'llaniladi — masalan bir marta ogohlantirilgandan keyin, xuddi shu coin uchun
keyingi ogohlantirish faqat CRYPTO_PRICE_ALERT_COOLDOWN_HOURS soatdan keyin yuboriladi.
"""

import logging
from datetime import datetime, timezone

import requests

from config import CRYPTO_COINS, CRYPTO_PRICE_ALERT_COOLDOWN_HOURS, CRYPTO_PRICE_CHANGE_THRESHOLD

logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

# Coin ID -> odam o'qiy oladigan nom
COIN_DISPLAY_NAMES = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)",
    "binancecoin": "BNB",
    "solana": "Solana (SOL)",
    "ripple": "XRP",
}


def fetch_prices() -> list[dict] | None:
    """
    CRYPTO_COINS ro'yxatidagi coinlarning joriy narxi va 24 soatlik o'zgarishini yuklab oladi.
    Tarmoq xatosida None qaytaradi.
    """
    try:
        response = requests.get(
            COINGECKO_URL,
            params={
                "vs_currency": "usd",
                "ids": ",".join(CRYPTO_COINS),
                "price_change_percentage": "24h",
            },
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (forex-news-bot/1.0)"},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("Kripto narxlarini yuklab bo'lmadi: %s", exc)
        return None
    except ValueError as exc:
        logger.error("Kripto narx JSON formatini o'qib bo'lmadi: %s", exc)
        return None


def _state_key(coin_id: str) -> str:
    return f"crypto_price_{coin_id}"


def _cooldown_expired(state: dict, coin_id: str) -> bool:
    """Shu coin uchun oxirgi ogohlantirishdan CRYPTO_PRICE_ALERT_COOLDOWN_HOURS soat o'tganmi?"""
    entry = state.get(_state_key(coin_id))
    if not entry or "last_alert_at" not in entry:
        return True
    last_alert = datetime.fromisoformat(entry["last_alert_at"])
    hours_passed = (datetime.now(timezone.utc) - last_alert).total_seconds() / 3600
    return hours_passed >= CRYPTO_PRICE_ALERT_COOLDOWN_HOURS


def _mark_alerted(state: dict, coin_id: str, direction: str) -> None:
    state[_state_key(coin_id)] = {
        "last_alert_at": datetime.now(timezone.utc).isoformat(),
        "last_direction": direction,
    }


def check_price_alerts(state: dict) -> list[dict]:
    """
    Narxlarni tekshiradi va chegaradan oshgan, cooldown tugagan coinlar uchun
    ogohlantirish kerak bo'lgan ma'lumotlar ro'yxatini qaytaradi:
    [{"coin_id", "display_name", "price", "change_24h", "direction"}]
    """
    prices = fetch_prices()
    if prices is None:
        return []

    alerts = []
    for coin in prices:
        coin_id = coin.get("id", "")
        change = coin.get("price_change_percentage_24h")
        price = coin.get("current_price")

        if change is None or price is None:
            continue
        if abs(change) < CRYPTO_PRICE_CHANGE_THRESHOLD:
            continue
        if not _cooldown_expired(state, coin_id):
            continue

        direction = "up" if change > 0 else "down"
        alerts.append(
            {
                "coin_id": coin_id,
                "display_name": COIN_DISPLAY_NAMES.get(coin_id, coin.get("name", coin_id)),
                "price": price,
                "change_24h": change,
                "direction": direction,
            }
        )
        _mark_alerted(state, coin_id, direction)
        logger.info("Kripto ogohlantirish: %s %+.1f%% (24s)", coin_id, change)

    return alerts
