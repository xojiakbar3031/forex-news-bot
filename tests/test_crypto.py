from datetime import datetime, timedelta, timezone

import crypto_news
import crypto_price


def _news(*ids):
    return [{"id": i, "title": i, "link": i, "summary": ""} for i in ids]


def test_news_bootstrap_sends_nothing_then_only_new(monkeypatch):
    state = {}
    monkeypatch.setattr(crypto_news, "fetch_news", lambda: _news("c", "b", "a"))
    assert crypto_news.check_new_news(state) == []

    monkeypatch.setattr(crypto_news, "fetch_news", lambda: _news("e", "d", "c", "b"))
    assert [n["id"] for n in crypto_news.check_new_news(state)] == ["d", "e"]  # eskidan yangiga
    assert crypto_news.check_new_news(state) == []


def test_price_alert_threshold_and_cooldown(monkeypatch):
    prices = [
        {"id": "bitcoin", "current_price": 100_000, "price_change_percentage_24h": -7.2},
        {"id": "ethereum", "current_price": 4_000, "price_change_percentage_24h": 1.0},
    ]
    monkeypatch.setattr(crypto_price, "fetch_prices", lambda: prices)
    state = {}

    alerts = crypto_price.check_price_alerts(state)
    assert [(a["coin_id"], a["direction"]) for a in alerts] == [("bitcoin", "down")]
    assert crypto_price.check_price_alerts(state) == []  # cooldown

    old = datetime.now(timezone.utc) - timedelta(hours=crypto_price.CRYPTO_PRICE_ALERT_COOLDOWN_HOURS + 1)
    state["crypto_price_bitcoin"]["last_alert_at"] = old.isoformat()
    assert len(crypto_price.check_price_alerts(state)) == 1
