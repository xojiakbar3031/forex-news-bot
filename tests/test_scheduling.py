from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture
def sent(monkeypatch):
    log = []
    monkeypatch.setattr(main, "send_message", lambda text: log.append(text) or True)
    monkeypatch.setattr(main, "build_reminder_message", lambda e, m: f"reminder {m}")
    monkeypatch.setattr(main, "build_actual_message", lambda e: "actual")
    return log


def _event(minutes_from_now, actual=""):
    return {
        "event_id": "2026-08-12_CPI m/m",
        "title": "CPI m/m",
        "time_tashkent": datetime.now(main.TASHKENT_TZ) + timedelta(minutes=minutes_from_now),
        "actual": actual,
    }


def test_sends_15_min_reminder_once(sent):
    state = {}
    main.process_event(_event(10), state)
    main.process_event(_event(10), state)
    assert sent == ["reminder 15"]
    assert state["2026-08-12_CPI m/m"]["reminder_15_sent"] is True


def test_sends_both_reminders_inside_5_min_window(sent):
    state = {}
    main.process_event(_event(3), state)
    assert sorted(sent) == ["reminder 15", "reminder 5"]


def test_no_reminder_far_in_advance(sent):
    main.process_event(_event(60), {})
    assert sent == []


def test_sends_actual_when_published(sent):
    state = {}
    main.process_event(_event(-1, actual="0.4%"), state)
    main.process_event(_event(-1, actual="0.4%"), state)
    assert sent == ["actual"]


def test_waits_for_actual_then_gives_up(sent):
    state = {}
    main.process_event(_event(-2), state)
    assert "2026-08-12_CPI m/m" not in state  # hali kutyapti
    main.process_event(_event(-(main.LIVE_POLL_TIMEOUT_MINUTES + 1)), state)
    assert sent == []
    assert state["2026-08-12_CPI m/m"]["actual_sent"] is True


def test_cleanup_keeps_newest_entries(monkeypatch):
    monkeypatch.setattr(main, "MAX_STATE_ENTRIES", 2)
    state = {"2026-08-01_A": {}, "2026-08-03_B": {}, "2026-08-02_C": {}}
    assert set(main._cleanup_old_state(state)) == {"2026-08-03_B", "2026-08-02_C"}
