"""
state.py — Bot "xotirasi". Qaysi voqea uchun qaysi xabar allaqachon yuborilganini
state.json faylida saqlaydi. Shu tufayli bot qayta ishga tushsa ham,
bir xil xabarni ikki marta yubormaydi.

state.json ichida har bir voqea shu ko'rinishda saqlanadi:
{
  "2026-08-17_CPI m/m": {
    "reminder_15_sent": true,
    "reminder_5_sent": true,
    "actual_sent": false
  }
}
"""

import json
import logging
import os

from config import STATE_FILE

logger = logging.getLogger(__name__)


def load_state() -> dict:
    """state.json faylini o'qib, Python lug'ati (dict) shaklida qaytaradi."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("state.json faylini o'qib bo'lmadi (%s). Bo'sh holatdan boshlanadi.", exc)
        return {}


def save_state(state: dict) -> None:
    """Joriy holatni state.json fayliga yozadi."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        logger.error("state.json faylini saqlab bo'lmadi: %s", exc)


def get_event_state(state: dict, event_id: str) -> dict:
    """Berilgan voqea uchun holatni qaytaradi, mavjud bo'lmasa — bo'shini yaratadi."""
    return state.get(
        event_id,
        {"reminder_15_sent": False, "reminder_5_sent": False, "actual_sent": False},
    )


def set_event_flag(state: dict, event_id: str, flag_name: str) -> None:
    """Berilgan voqea uchun bitta bayroqni (masalan 'actual_sent') True qilib belgilaydi."""
    event_state = get_event_state(state, event_id)
    event_state[flag_name] = True
    state[event_id] = event_state
