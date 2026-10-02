import requests

import parser


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


FEED = [
    {"title": "CPI m/m", "country": "USD", "impact": "High",
     "date": "2026-08-12T08:30:00-04:00", "forecast": "0.3%", "previous": "0.2%", "actual": ""},
    {"title": "CPI m/m", "country": "EUR", "impact": "High",       # boshqa valyuta
     "date": "2026-08-12T05:00:00-04:00"},
    {"title": "Retail Sales m/m", "country": "USD", "impact": "High",  # ro'yxatda yo'q
     "date": "2026-08-14T08:30:00-04:00"},
    {"title": "Unemployment Rate", "country": "USD", "impact": "Medium",  # ta'siri past
     "date": "2026-08-07T08:30:00-04:00"},
    {"title": "Non-Farm Employment Change", "country": "USD", "impact": "High",
     "date": "2026-08-07T08:30:00-04:00", "forecast": "180K", "previous": "150K", "actual": "210K"},
    {"title": "FOMC Statement", "country": "USD", "impact": "High"},  # sana yo'q -> o'tkaziladi
]


def test_filters_usd_high_impact_relevant_events(monkeypatch):
    monkeypatch.setattr(parser.requests, "get", lambda *a, **k: _Resp(FEED))
    events = parser.fetch_events()

    assert [e["title"] for e in events] == ["CPI m/m", "Non-Farm Employment Change"]
    cpi = events[0]
    # 08:30 New York (EDT) = 17:30 Toshkent
    assert cpi["time_tashkent"].strftime("%Y-%m-%d %H:%M") == "2026-08-12 17:30"
    assert cpi["event_id"] == "2026-08-12_CPI m/m"
    assert cpi["actual"] == ""
    assert events[1]["actual"] == "210K"


def test_network_error_returns_none(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(parser.requests, "get", boom)
    assert parser.fetch_events() is None
