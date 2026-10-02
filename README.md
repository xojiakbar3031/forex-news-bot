# Forex News Bot 📈

A Telegram bot that runs 24/7 and posts **high-impact US economic events** (CPI, NFP,
FOMC, GDP, PPI…) to a channel. It warns before each release, publishes the actual
figure the moment it appears, and compares it with the forecast. It also tracks sharp
crypto price moves and crypto headlines. All messages are translated into **Uzbek** for
local traders.

## What it posts

| Trigger | Message |
|---|---|
| 15 and 5 minutes before a red-folder USD event | reminder with forecast and previous value |
| Actual figure published | actual vs forecast, with "higher / lower / in line" |
| BTC, ETH, BNB, SOL or XRP moves ≥ 5 % in 24 h | price alert (4 h cooldown per coin) |
| New CoinTelegraph headline | translated headline + link |

Times are converted to Tashkent time. Event titles use a hand-curated glossary for the
common indicators and fall back to machine translation for everything else.

## Design

```
ForexFactory JSON ─► parser (USD · High · keyword filter · TZ convert)
CoinGecko API     ─► price alerts (threshold + cooldown)        ─► messages (HTML, escaped)
CoinTelegraph RSS ─► news (bootstrap-safe dedupe)                         │
                                                                          ▼
                      state.json  ◄── idempotency flags ──  notifier (retry ×3) ─► Telegram
```

- **Idempotent.** Every message sent is recorded in `state.json`, so restarts and
  redeploys never send a message twice. The state is capped by entry count, not by
  age, because the feed sometimes returns events from days ago.
- **Fails safely.** Network errors trigger a back-off (the free feed answers
  `429` if polled too often). Unexpected exceptions are logged and the loop keeps
  running. If an actual figure doesn't appear within 10 minutes, the bot stops
  waiting for it.
- **Bootstrap-safe news.** On the first run the bot marks the existing RSS items as
  seen instead of flooding the channel with them.
- **Free-tier hosting.** A tiny health-check HTTP server lets it run as a Render free
  Web Service that an uptime pinger keeps awake.

## Run locally

```bash
python -m venv venv && venv\Scripts\activate     # source venv/bin/activate on Linux/macOS
pip install -r requirements.txt
cp .env.example .env    # BOT_TOKEN from @BotFather, CHANNEL_ID of your channel
python main.py
```

If `BOT_TOKEN` is not set, messages are printed to the console instead of being sent,
which is handy for trying it out. Filters, intervals, coins and thresholds are all set
in [`config.py`](config.py).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests cover feed filtering and timezone conversion, reminder and actual-figure
timing, deduplication, crypto alert cooldowns, news bootstrap and HTML escaping.

## Deploy (Render)

`render.yaml` is included. Create a Web Service from the repo, set `BOT_TOKEN` and
`CHANNEL_ID`, then point a free uptime monitor (for example UptimeRobot) at the
service URL every 5 minutes.

## Stack

Python 3.11 · python-telegram-bot · requests · feedparser · deep-translator · pytz · pytest

## License

MIT
