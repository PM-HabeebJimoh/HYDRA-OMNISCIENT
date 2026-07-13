---
name: Telegram alerts integration
description: How Telegram alerts are wired into HYDRA-S3; credentials, dedup, async patterns
---

# Telegram Alerts — HYDRA-S3

**Rule:** TELEGRAM_TOKEN stored as Replit Secret; TELEGRAM_CHAT_ID as shared env var. Never hardcoded in any file.

**Module:** `core/telegram_alerts.py`
- Async sender (`send_alert_async`) for live_engine.py (already in an event loop)
- Sync wrapper (`send_alert_sync`) for Streamlit UI (uses ThreadPoolExecutor to avoid event-loop conflict)
- `dispatch_opportunity_alert()` deduplicates INEVITABLE by opp_id; HIGH CONVICTION has 5-min per-asset cooldown

**Why:** Streamlit runs its own event loop internally, so calling `asyncio.run()` directly from a button handler crashes. The ThreadPoolExecutor pattern spawns a fresh loop in a worker thread.

**How to apply:** Any new alert type — add a formatter (`fmt_*`), call `send_alert_sync` from UI or `send_alert_async` from daemon.

**Test panel:** System Configuration module has "SEND TEST ALERT" and "DEMO INEVITABLE ALERT" buttons, gated on credentials being present.
