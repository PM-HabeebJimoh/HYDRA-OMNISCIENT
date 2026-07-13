"""
HYDRA-S3 Telegram Alert System
Credentials sourced exclusively from Replit Secrets — never hardcoded.
"""
import os
import asyncio
import logging
import aiohttp
from datetime import datetime

logger = logging.getLogger('HYDRA-S3-TELEGRAM')

# ── Credentials from environment (set as Replit Secrets) ─────────────────────
TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
_BASE_URL        = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ── Deduplication: track last-sent opp IDs to avoid spam ─────────────────────
_sent_ids: set = set()
_last_high_conviction: dict = {}   # asset → last-sent epoch


# ── Core sender ───────────────────────────────────────────────────────────────
async def _send(message: str) -> bool:
    """Low-level async Telegram send. Returns True on success."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured — missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID")
        return False
    try:
        url     = f"{_BASE_URL}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get('ok'):
                    logger.info("Telegram alert sent OK")
                    return True
                logger.error(f"Telegram API error: {data.get('description', data)}")
                return False
    except Exception as e:
        logger.error(f"Telegram send exception: {e}")
        return False


def send_alert_sync(message: str) -> bool:
    """Synchronous wrapper — safe to call from Streamlit (non-async context)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Running inside an existing event loop (e.g. Streamlit internals)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, _send(message))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_send(message))
    except Exception:
        try:
            return asyncio.run(_send(message))
        except Exception as e:
            logger.error(f"Telegram sync wrapper failed: {e}")
            return False


async def send_alert_async(message: str) -> bool:
    """Direct async send — use this from live_engine.py."""
    return await _send(message)


# ── Alert formatters ──────────────────────────────────────────────────────────
def _ts() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d  %H:%M:%S  UTC')

def _dir(direction: int) -> str:
    return "▲ LONG" if direction == 1 else "▼ SHORT" if direction == -1 else "— NEUTRAL"


def fmt_inevitable(asset: str, score: float, regime: str, direction: int, opp_id: str) -> str:
    return (
        f"🚨 <b>S-ALERT: CONVERGENCE INEVITABLE</b>\n\n"
        f"🔱 <b>HYDRA-S3 ENTERPRISE QUANT TERMINAL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>ASSET   :</b> {asset}\n"
        f"📊 <b>SCORE   :</b> {score:.4f}  🔴\n"
        f"🌐 <b>REGIME  :</b> {regime}\n"
        f"🎯 <b>BIAS    :</b> {_dir(direction)}\n"
        f"🆔 <b>OPP ID  :</b> <code>{opp_id}</code>\n"
        f"⏰ <b>TIME    :</b> {_ts()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>Immediate execution window open — check Matrix Dashboard</i>"
    )


def fmt_high_conviction(asset: str, score: float, regime: str, direction: int) -> str:
    return (
        f"🟡 <b>HIGH CONVICTION SETUP DETECTED</b>\n\n"
        f"🔱 <b>HYDRA-S3 ENTERPRISE QUANT TERMINAL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>ASSET   :</b> {asset}\n"
        f"📊 <b>SCORE   :</b> {score:.4f}\n"
        f"🌐 <b>REGIME  :</b> {regime}\n"
        f"🎯 <b>BIAS    :</b> {_dir(direction)}\n"
        f"⏰ <b>TIME    :</b> {_ts()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <i>Monitor for INEVITABLE confirmation</i>"
    )


def fmt_trade_executed(asset: str, direction: int, size: float,
                        entry: float, sl: float, tp: float, score: float) -> str:
    return (
        f"✅ <b>TRADE EXECUTED</b>\n\n"
        f"🔱 <b>HYDRA-S3 ENTERPRISE QUANT TERMINAL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>ASSET   :</b> {asset}\n"
        f"🎯 <b>SIDE    :</b> {_dir(direction)}\n"
        f"📊 <b>SCORE   :</b> {score:.4f}\n"
        f"💰 <b>ENTRY   :</b> ${entry:,.4f}\n"
        f"🛑 <b>STOP    :</b> ${sl:,.4f}\n"
        f"🎯 <b>TARGET  :</b> ${tp:,.4f}\n"
        f"📦 <b>SIZE    :</b> {size:.4f}\n"
        f"⏰ <b>TIME    :</b> {_ts()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def fmt_startup() -> str:
    return (
        f"✅ <b>HYDRA-S3 DAEMON ACTIVATED</b>\n\n"
        f"🔱 <b>HYDRA-S3 ENTERPRISE QUANT OS v4.0</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 Engine: S3-RHGNN v4.0  ONLINE\n"
        f"📡 Mode:   24/7 Multi-Asset Monitor\n"
        f"🔔 Alerts: Telegram ACTIVE\n"
        f"⏰ Start:  {_ts()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Monitoring 5 asset streams. All alert channels live.</i>"
    )


def fmt_test() -> str:
    return (
        f"🧪 <b>HYDRA-S3 ALERT TEST — SYSTEMS CHECK</b>\n\n"
        f"🔱 <b>HYDRA-S3 ENTERPRISE QUANT TERMINAL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Telegram integration: VERIFIED\n"
        f"✅ Chat ID:              ACTIVE\n"
        f"✅ Token:                VALID\n"
        f"⏰ Timestamp:           {_ts()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>All alert channels operational. Ready for live monitoring.</i>"
    )


# ── Smart alert dispatchers (called from live_engine) ─────────────────────────
async def dispatch_opportunity_alert(asset: str, score: float, regime: str,
                                      direction: int, status: str, opp_id: str):
    """
    Called by the daemon for each qualifying opportunity.
    - INEVITABLE  → always alert (dedup by opp_id)
    - HIGH CONVICTION → alert at most once per 5 min per asset
    """
    global _sent_ids, _last_high_conviction

    if status == "INEVITABLE":
        if opp_id in _sent_ids:
            return
        _sent_ids.add(opp_id)
        # Bound memory: keep only latest 500 IDs
        if len(_sent_ids) > 500:
            _sent_ids = set(list(_sent_ids)[-500:])
        msg = fmt_inevitable(asset, score, regime, direction, opp_id)
        await send_alert_async(msg)

    elif status == "HIGH CONVICTION":
        import time
        now = time.time()
        last = _last_high_conviction.get(asset, 0)
        if now - last < 300:   # 5-minute cooldown per asset
            return
        _last_high_conviction[asset] = now
        msg = fmt_high_conviction(asset, score, regime, direction)
        await send_alert_async(msg)
