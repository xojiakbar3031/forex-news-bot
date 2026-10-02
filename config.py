"""
config.py — Botning barcha sozlamalari shu yerda.
Maxfiy ma'lumotlar (token, kanal ID) .env faylidan o'qiladi —
shuning uchun ular to'g'ridan-to'g'ri kodda ko'rinmaydi.
"""

import os
from dotenv import load_dotenv

# .env faylini o'qib, undagi qiymatlarni xotiraga yuklaydi
load_dotenv()

# --- Telegram sozlamalari ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

# --- Ma'lumot manbasi (ForexFactory ochiq JSON lentasi) ---
# Eslatma: topshiriqda ko'rsatilgan manzil (nfp.ourfocus.net) ishlamayapti,
# shuning uchun ForexFactory'ning haqiqiy, ishlaydigan ochiq lentasidan foydalanamiz.
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# --- Filtr sozlamalari ---
TARGET_CURRENCY = "USD"
TARGET_IMPACT = "High"  # Faqat qizil (yuqori ta'sirli) voqealar

# --- Vaqt zonasi ---
TIMEZONE = "Asia/Tashkent"

# --- Eslatma vaqtlari (voqeadan necha daqiqa oldin ogohlantirish) ---
REMINDER_MINUTES = [15, 5]

# --- Tsikl sozlamalari ---
# Eslatma: ForexFactory bepul lentasi juda tez-tez so'rov yuborilsa
# "429 Too Many Requests" bilan vaqtincha bloklashi kuzatildi (test paytida aniqlandi).
# 15 soniya rasmiy topshiriqda ko'rsatilgan, lekin xavfsizroq ishlashi uchun 20 soniya qilindi.
# Agar hech qanday muammo bo'lmasa, buni 15 ga qaytarishingiz mumkin.
CHECK_INTERVAL_SECONDS = 20          # Oddiy holatda har necha soniyada tekshirish
LIVE_POLL_INTERVAL_SECONDS = 20      # Voqea vaqti kelganda "actual" natijani kutish oralig'i
LIVE_POLL_TIMEOUT_MINUTES = 10       # Natijani necha daqiqa kutish (undan keyin bekor qilinadi)
RATE_LIMIT_BACKOFF_SECONDS = 60      # Tarmoq xatosi (masalan 429) bo'lsa, qo'shimcha kutish vaqti

# --- Kripto narx sozlamalari ---
# CoinGecko'dagi coin ID'lari (https://api.coingecko.com/api/v3/coins/list dan olinadi)
CRYPTO_COINS = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]
CRYPTO_PRICE_CHANGE_THRESHOLD = 5.0          # 24 soatlik o'zgarish shu % dan katta bo'lsa, ogohlantiriladi
CRYPTO_PRICE_CHECK_INTERVAL_SECONDS = 60     # Narxni har necha soniyada tekshirish
CRYPTO_PRICE_ALERT_COOLDOWN_HOURS = 4        # Bir xil coin uchun qayta ogohlantirishdan oldin necha soat kutish

# --- Kripto yangiliklar sozlamalari ---
CRYPTO_NEWS_FEED_URL = "https://cointelegraph.com/rss"
CRYPTO_NEWS_CHECK_INTERVAL_SECONDS = 300     # Yangiliklarni har necha soniyada tekshirish (5 daqiqa)
CRYPTO_NEWS_MAX_PER_CYCLE = 5                # Bir tekshiruvda ko'pi bilan nechta yangi xabar yuborish (spam bo'lmasin)

# --- Fayllar ---
STATE_FILE = "state.json"
