"""
messages.py — Telegramga yuboriladigan xabar matnlarini (shablonlarni) tayyorlaydi.
"""

from html import escape

from translator import translate_text, translate_title

# Xabarlar Telegram HTML formatida yuboriladi. Tashqi matnlar (tarjima, yangilik
# sarlavhasi) escape qilinadi — aks holda "_" yoki "<" kabi belgilar xabarni buzadi.


def _safe(value: str) -> str:
    """Bo'sh qiymatlarni chiroyli ko'rsatish uchun (HTML-xavfsiz)."""
    return escape(value) if value else "—"


def build_reminder_message(event: dict, minutes_before: int) -> str:
    """
    Voqeadan oldin yuboriladigan ogohlantirish xabari.
    """
    title_uz = escape(translate_title(event["title"]))
    return (
        f"⏰ <b>OGOHLANTIRISH: {minutes_before} daqiqadan so'ng muhim yangilik!</b>\n"
        f"📌 Voqea: {title_uz}\n"
        f"🌐 Davlat: AQSh ({event['country']})\n"
        f"🎯 Prognoz (Forecast): {_safe(event['forecast'])}\n"
        f"📜 Oldingi (Previous): {_safe(event['previous'])}\n"
        f"⚡️ Bozorda yuqori volatillashuv kutilmoqda!"
    )


def _compare_actual_vs_forecast(actual: str, forecast: str) -> str:
    """
    Natija bilan prognozni solishtirib, qisqacha izoh qaytaradi.
    Raqamni chiqarib olishga urinadi (masalan "0.4%" -> 0.4); bo'lmasa izohsiz qaytadi.
    """
    def _to_number(value: str):
        cleaned = value.replace("%", "").replace(",", "").replace("K", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    actual_num = _to_number(actual)
    forecast_num = _to_number(forecast)

    if actual_num is None or forecast_num is None:
        return "💡 Natija e'lon qilindi."

    if actual_num > forecast_num:
        return "💡 Natija prognozdan <b>yuqori</b> chiqdi."
    elif actual_num < forecast_num:
        return "💡 Natija prognozdan <b>past</b> chiqdi."
    else:
        return "💡 Natija prognoz bilan <b>bir xil</b> chiqdi."


def build_crypto_price_message(alert: dict) -> str:
    """
    Kriptovalyuta narxi keskin o'zgarganda yuboriladigan xabar.
    `alert` — crypto_price.check_price_alerts() qaytargan bitta element.
    """
    direction_emoji = "🟢📈" if alert["direction"] == "up" else "🔴📉"
    direction_word = "ko'tarildi" if alert["direction"] == "up" else "tushdi"
    return (
        f"{direction_emoji} <b>KESKIN NARX O'ZGARISHI!</b>\n"
        f"🪙 Coin: {escape(alert['display_name'])}\n"
        f"💵 Narx: ${alert['price']:,.2f}\n"
        f"📊 24 soatlik o'zgarish: <b>{alert['change_24h']:+.1f}%</b> ({direction_word})"
    )


def build_crypto_news_message(item: dict) -> str:
    """
    Yangi kripto yangilik chiqqanda yuboriladigan xabar.
    `item` — crypto_news.check_new_news() qaytargan bitta element ({"title", "link", "summary"}).
    """
    title_uz = escape(translate_text(item["title"]))
    return f"📰 <b>Kripto yangilik</b>\n\n{title_uz}\n\n🔗 {escape(item['link'])}"


def build_actual_message(event: dict) -> str:
    """
    Voqea natijasi (actual) e'lon qilinganda yuboriladigan asosiy xabar.
    """
    title_uz = escape(translate_title(event["title"]))
    comparison = _compare_actual_vs_forecast(event["actual"], event["forecast"])
    return (
        f"🚨 <b>AQSH MUHIM IQTISODIY KO'RSATKICHI!</b>\n"
        f"📊 Voqea: {title_uz}\n"
        f"🔴 Natija (Actual): <b>{_safe(event['actual'])}</b>\n"
        f"🎯 Prognoz (Forecast): {_safe(event['forecast'])}\n"
        f"📜 Oldingi (Previous): {_safe(event['previous'])}\n"
        f"{comparison}"
    )
