"""
translator.py — Inglizcha voqea nomlarini o'zbek tiliga tarjima qiladi.

Eslatma: ba'zi moliyaviy atamalar (CPI, NFP, FOMC kabi) traderlar orasida
qisqartma holida keng tanilgan, shuning uchun ularni tarjima qilmay,
tayyor lug'atdan foydalanamiz — bu tez ham, aniq ham ishlaydi.
Lug'atda yo'q nom uchun avtomatik tarjimonga (Google Translate) murojaat qilinadi.
"""

import logging

from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# Eng ko'p uchraydigan voqealar uchun tayyor, sifatli tarjima (tezroq va aniqroq)
KNOWN_TRANSLATIONS = {
    "CPI m/m": "Iste'mol narxlari indeksi (CPI m/m)",
    "CPI y/y": "Iste'mol narxlari indeksi (CPI y/y)",
    "Core CPI m/m": "Bazaviy iste'mol narxlari indeksi (Core CPI m/m)",
    "Core CPI y/y": "Bazaviy iste'mol narxlari indeksi (Core CPI y/y)",
    "PPI m/m": "Ishlab chiqaruvchi narxlar indeksi (PPI m/m)",
    "Core PPI m/m": "Bazaviy ishlab chiqaruvchi narxlar indeksi (Core PPI m/m)",
    "Non-Farm Employment Change": "Qishloq xo'jaligidan tashqari ish o'rinlari (NFP)",
    "Unemployment Rate": "Ishsizlik darajasi",
    "Average Hourly Earnings m/m": "O'rtacha soatlik ish haqi (m/m)",
    "FOMC Statement": "FOMC bayonoti (FRS qarori)",
    "FOMC Press Conference": "FOMC matbuot anjumani",
    "Federal Funds Rate": "Federal fond stavkasi",
    "GDP q/q": "Yalpi ichki mahsulot (GDP, chorak)",
    "Prelim GDP q/q": "Yalpi ichki mahsulot, dastlabki (GDP, chorak)",
}


def translate_title(title: str) -> str:
    """
    Voqea nomini o'zbek tiliga tarjima qiladi.
    Avval tayyor lug'atdan qaraydi, topilmasa Google Translate orqali tarjima qiladi.
    """
    if title in KNOWN_TRANSLATIONS:
        return KNOWN_TRANSLATIONS[title]

    try:
        translated = GoogleTranslator(source="en", target="uz").translate(title)
        return f"{translated} ({title})"
    except Exception as exc:  # tarmoq/tarjima xizmati vaqtinchalik ishlamasligi mumkin
        logger.warning("Tarjima qilishda xatolik ('%s'): %s. Original nom ishlatiladi.", title, exc)
        return title


def translate_text(text: str) -> str:
    """Har qanday erkin matnni o'zbek tiliga tarjima qiladi (masalan tahlil izohlari uchun)."""
    if not text:
        return text
    try:
        return GoogleTranslator(source="en", target="uz").translate(text)
    except Exception as exc:
        logger.warning("Matnni tarjima qilishda xatolik: %s", exc)
        return text
