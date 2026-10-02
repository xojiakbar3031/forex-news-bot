import os
import sys

# Testlar haqiqiy Telegram'ga xabar yubormasligi uchun tokenlarni bo'shatamiz
os.environ["BOT_TOKEN"] = ""
os.environ["CHANNEL_ID"] = ""
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
