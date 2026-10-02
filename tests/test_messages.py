import messages


def _event(**kw):
    base = {"title": "CPI m/m", "country": "USD", "forecast": "0.3%", "previous": "0.2%", "actual": "0.4%"}
    base.update(kw)
    return base


def test_compare_actual_vs_forecast():
    cmp = messages._compare_actual_vs_forecast
    assert "yuqori" in cmp("0.4%", "0.3%")
    assert "past" in cmp("150K", "180K")
    assert "bir xil" in cmp("1,200", "1200")
    assert cmp("", "0.3%") == "💡 Natija e'lon qilindi."


def test_actual_message_is_html_escaped(monkeypatch):
    monkeypatch.setattr(messages, "translate_title", lambda t: "Test <b>_x_</b> & y")
    text = messages.build_actual_message(_event(actual="<0.4%>"))
    assert "Test &lt;b&gt;_x_&lt;/b&gt; &amp; y" in text
    assert "<b>&lt;0.4%&gt;</b>" in text


def test_reminder_message_shows_dash_for_missing_values(monkeypatch):
    monkeypatch.setattr(messages, "translate_title", lambda t: t)
    text = messages.build_reminder_message(_event(forecast="", previous=""), 15)
    assert "15 daqiqadan" in text
    assert text.count("—") == 2


def test_news_message_escapes_title(monkeypatch):
    monkeypatch.setattr(messages, "translate_text", lambda t: t)
    text = messages.build_crypto_news_message({"title": "BTC > $100k", "link": "https://x.io/?a=1&b=2"})
    assert "BTC &gt; $100k" in text
    assert "a=1&amp;b=2" in text
