"""
HYDRA-S3  |  Enterprise Telegram Alert System  v5.0
Exact alert template as specified — 3-section structured format.
Credentials sourced exclusively from Replit Secrets/Env.
"""
import os
import asyncio
import logging
import time
from datetime import datetime, timezone

import aiohttp

logger = logging.getLogger('HYDRA-S3-TELEGRAM')

# ── Credentials ────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
_BASE_URL        = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ── Deduplication ──────────────────────────────────────────────────────────────
_sent_ids:            set  = set()
_last_high_conv:      dict = {}   # asset → epoch timestamp
_alert_seq:           int  = 0


# ══════════════════════════════════════════════════════════════════════════════
#  CORE SEND
# ══════════════════════════════════════════════════════════════════════════════

async def _send(text: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured — token or chat_id missing")
        return False
    try:
        url     = f"{_BASE_URL}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
        timeout = aiohttp.ClientTimeout(total=14)
        async with aiohttp.ClientSession(timeout=timeout) as sess:
            async with sess.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get('ok'):
                    logger.info("Telegram alert delivered ✓")
                    return True
                logger.error(f"Telegram API error: {data.get('description', data)}")
                return False
    except Exception as e:
        logger.error(f"Telegram send exception: {e}")
        return False


def send_alert_sync(text: str) -> bool:
    """Sync wrapper — safe to call from Streamlit."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _send(text)).result(timeout=16)
        return loop.run_until_complete(_send(text))
    except Exception:
        try:
            return asyncio.run(_send(text))
        except Exception as e:
            logger.error(f"Telegram sync wrapper failed: {e}")
            return False


async def send_alert_async(text: str) -> bool:
    return await _send(text)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _ts() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

def _seq() -> int:
    global _alert_seq
    _alert_seq += 1
    return _alert_seq

def _score_bar(score: float, w: int = 14) -> str:
    filled = round(score * w)
    return '█' * filled + '░' * (w - filled)

def _session() -> str:
    h = datetime.now(timezone.utc).hour
    if   13 <= h < 16: return "NY/LONDON OVERLAP ⚡"
    elif  8 <= h < 13: return "LONDON SESSION 🇬🇧"
    elif 13 <= h < 21: return "NEW YORK SESSION 🇺🇸"
    elif  0 <= h <  8: return "ASIAN SESSION 🌏"
    return "OFF-HOURS 🌙"

def _bias(direction: int) -> tuple[str, str]:
    if direction == 1:  return "🟢", "▲ LONG  / BUY"
    if direction == -1: return "🔴", "▼ SHORT / SELL"
    return "⚪", "— NEUTRAL"

def _regime_mult(regime: str) -> float:
    if "CONTRACTION" in regime: return 1.5
    if "EXPANSION"   in regime: return 1.2
    return 1.0

def _leverage(score: float, regime: str) -> float:
    base = 100.0 if score >= 0.95 else 50.0 if score >= 0.80 else 10.0
    return base * _regime_mult(regime)

def _tp_range(score: float) -> str:
    return "10% - 20%" if score >= 0.95 else "5% - 10%"


# ══════════════════════════════════════════════════════════════════════════════
#  PRIMARY ALERT TEMPLATE  —  Exact spec from user requirements
# ══════════════════════════════════════════════════════════════════════════════

def fmt_s3_convergence(
    asset:        str,
    opp_id:       str,
    score:        float,
    status:       str,
    regime:       str,
    direction:    int,
    trigger_type: str      = "NEW_SIGNAL",
    world_state:  dict     = None,
    latent_sum:   float    = 0.0,
    equity:       float    = 100000.0,
    timestamp:    str      = None,
) -> str:
    """
    Exact Telegram alert template as specified:
      1. CORE SIGNAL
      2. EXECUTION SPECS
      3. CAUSAL SNAPSHOT
      [ ACTION: EXECUTE HYPER-TRADE NOW ]
    """
    ws         = world_state or {}
    ts         = timestamp or _ts()
    seq        = _seq()
    bar        = _score_bar(score)
    bias_em, bias_txt = _bias(direction)
    lev        = _leverage(score, regime)
    mult       = _regime_mult(regime)
    tp_rng     = _tp_range(score)
    ry         = ws.get('RealYield')
    obi        = ws.get('OBI')
    risk_cap   = equity * 0.02

    # Header — INEVITABLE gets 🚨 S-ALERT, HIGH CONVICTION gets 🟡
    if status == "INEVITABLE":
        hdr_em  = "🚨"
        hdr_txt = "[S-ALERT: CONVERGENCE INEVITABLE]"
    else:
        hdr_em  = "🟡"
        hdr_txt = "[S-ALERT: CONVERGENCE DETECTED]"

    ry_str  = f"{ry:.3f}%  (10Y TIPS)"    if ry  is not None else "⚠ OFFLINE"
    obi_str = f"{obi:+.4f}"               if obi is not None else "⚠ OFFLINE"
    if obi is not None:
        obi_dir = "SELL PRESSURE" if obi < -0.5 else "BUY PRESSURE" if obi > 0.5 else "BALANCED"
        obi_str = f"{obi:+.4f}  ({obi_dir})"

    _nasa   = ws.get('NASA')
    _eia    = ws.get('EIA')
    _aq     = ws.get('OpenAQ')
    _eth    = ws.get('ETH')
    nasa_str  = f"{_nasa:.4f}"   if _nasa  is not None else "⚠ OFFLINE"
    eia_str   = f"{_eia:.4f}"    if _eia   is not None else "⚠ OFFLINE"
    aq_str    = f"{_aq:.4f}"     if _aq    is not None else "⚠ OFFLINE"
    eth_str   = f"{_eth:.4f}"    if _eth   is not None else "⚠ OFFLINE"

    return (
        f"{hdr_em} <b>{hdr_txt}</b> 🔱\n"
        f"<b>ID:</b> <code>{opp_id}</code>\n"
        f"<b>Seq:</b> #{seq:04d}  |  <b>Trigger:</b> {trigger_type}\n"
        f"<b>Timestamp:</b> {ts}\n"
        f"<b>Session:</b> {_session()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>1. CORE SIGNAL</b>\n"
        f"<b>ASSET:</b>     {asset}\n"
        f"<b>BIAS:</b>      {bias_em} <b>{bias_txt}</b>\n"
        f"<b>S3 SCORE:</b>  <code>{score:.4f}</code>  {bar}  {score*100:.1f}%\n"
        f"<b>STATUS:</b>    {status}\n"
        f"<b>REGIME:</b>    {regime}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>2. EXECUTION SPECS</b>\n"
        f"<b>SUGGESTED LEVERAGE:</b>  {lev:.0f}x\n"
        f"<b>CAPITAL AT RISK:</b>     ${risk_cap:,.2f}  (2% rule)\n"
        f"<b>STOP-LOSS (SL):</b>      1% Hard Stop\n"
        f"<b>TARGET (TP):</b>         {tp_rng} Gain\n"
        f"<b>RISK/REWARD:</b>         {float(tp_rng.split('%')[0]):.0f}:1 minimum\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>3. CAUSAL SNAPSHOT</b>\n"
        f"<b>Real Yield:</b>          {ry_str}\n"
        f"<b>OBI (L2 Depth):</b>      {obi_str}\n"
        f"<b>Regime Multiplier:</b>   {mult:.1f}x\n"
        f"<b>Latent Energy:</b>       {latent_sum:.2f}\n"
        f"<b>NASA Fires:</b>          {nasa_str}\n"
        f"<b>EIA Energy:</b>          {eia_str}\n"
        f"<b>Industrial AQ:</b>       {aq_str}\n"
        f"<b>ETH On-Chain:</b>        {eth_str}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>[ ACTION: EXECUTE HYPER-TRADE NOW ]</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔱 HYDRA-S3 ENTERPRISE QUANT OS v5.0  ·  #LIVE"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  SECONDARY FORMATTERS
# ══════════════════════════════════════════════════════════════════════════════

def fmt_trade_executed(asset: str, direction: int, size: float,
                        entry: float, sl: float, tp: float, score: float,
                        equity: float = 100000.0, regime: str = "STABILITY") -> str:
    seq     = _seq()
    pnl_sl  = abs(entry - sl)  * size
    pnl_tp  = abs(tp - entry)  * size
    rr      = pnl_tp / max(pnl_sl, 0.01)
    bias_em, bias_txt = _bias(direction)
    return (
        f"✅ <b>[TRADE EXECUTED] #{seq:04d}</b> 🔱\n"
        f"<b>Timestamp:</b> {_ts()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ORDER DETAILS</b>\n"
        f"<b>ASSET:</b>      {asset}\n"
        f"<b>BIAS:</b>       {bias_em} {bias_txt}\n"
        f"<b>REGIME:</b>     {regime}\n"
        f"<b>S3 SCORE:</b>   <code>{score:.4f}</code>\n"
        f"<b>SESSION:</b>    {_session()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>PRICE LEVELS</b>\n"
        f"<b>ENTRY:</b>      ${entry:,.4f}\n"
        f"<b>STOP-LOSS:</b>  ${sl:,.4f}  (risk ${pnl_sl:,.2f})\n"
        f"<b>TAKE-PROFIT:</b>${tp:,.4f}  (target ${pnl_tp:,.2f})\n"
        f"<b>SIZE:</b>       {size:.4f} units\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>RISK SUMMARY</b>\n"
        f"<b>RISK/REWARD:</b>  {rr:.1f}:1\n"
        f"<b>MAX LOSS:</b>     ${pnl_sl:,.2f}\n"
        f"<b>MAX PROFIT:</b>   ${pnl_tp:,.2f}\n"
        f"<b>EQUITY:</b>       ${equity:,.2f}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔱 HYDRA-S3 ENTERPRISE QUANT OS v5.0  ·  #LIVE"
    )


def fmt_startup(asset_count: int = 5) -> str:
    return (
        f"🟢 <b>[HYDRA-S3 DAEMON ACTIVATED]</b> 🔱\n"
        f"<b>Timestamp:</b> {_ts()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>SYSTEM STATUS</b>\n"
        f"🟢 <b>Engine:</b>    S3-RHGNN v5.0  ONLINE\n"
        f"🟢 <b>Mode:</b>      24/7 LIVE MULTI-ASSET\n"
        f"🟢 <b>Assets:</b>    {asset_count} streams active\n"
        f"🟢 <b>Alerts:</b>    TELEGRAM ARMED\n"
        f"<b>Session:</b>   {_session()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>LIVE SIGNAL SOURCES</b>\n"
        f"  🌋 NASA EONET   — Global Wildfire Events\n"
        f"  ⚡ EIA Energy   — US Petroleum Price\n"
        f"  🏭 OpenAQ/WAQI  — Industrial PM2.5 AQ\n"
        f"  💎 OKX ETH      — ETHUSDT Funding Rate\n"
        f"  💵 US Treasury  — 10Y TIPS Real Yield\n"
        f"  📉 Kraken OBI   — BTC/USD L2 Imbalance\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>ALL CHANNELS ARMED. MONITORING LIVE.</b>\n"
        f"🔱 HYDRA-S3 ENTERPRISE QUANT OS v5.0"
    )


def fmt_test(equity: float = 100000.0) -> str:
    return (
        f"🧪 <b>[ALERT SYSTEM TEST]</b> 🔱\n"
        f"<b>Timestamp:</b> {_ts()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>INTEGRATION CHECK</b>\n"
        f"✅ Telegram Token  : VALID\n"
        f"✅ Chat ID         : ACTIVE\n"
        f"✅ HTML Parse Mode : ENABLED\n"
        f"✅ Alert Sequencer : #{_alert_seq + 1}\n"
        f"✅ Equity          : ${equity:,.2f}\n"
        f"✅ Session         : {_session()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ALERT TYPES ACTIVE</b>\n"
        f"  🚨 INEVITABLE       — S-ALERT + Dedup by ID\n"
        f"  🟡 HIGH CONVICTION  — 5-min asset cooldown\n"
        f"  ✅ TRADE EXECUTED   — Every position open\n"
        f"  🟢 DAEMON STARTUP   — On engine restart\n"
        f"  💓 HEARTBEAT        — Every 60 cycles\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>ALL SYSTEMS OPERATIONAL</b>\n"
        f"🔱 HYDRA-S3 ENTERPRISE QUANT OS v5.0  ·  #TEST"
    )


def fmt_heartbeat(cycle: int, asset_count: int, opportunities: int,
                   equity: float = 100000.0, signals_live: int = 0) -> str:
    return (
        f"💓 <b>[SYSTEM HEARTBEAT]</b> 🔱\n"
        f"<b>Timestamp:</b> {_ts()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ENGINE STATUS</b>\n"
        f"<b>Scan Cycles:</b>   {cycle:,}\n"
        f"<b>Assets Live:</b>   {asset_count}\n"
        f"<b>Signals Live:</b>  {signals_live}/6\n"
        f"<b>Opportunities:</b> {opportunities} total\n"
        f"<b>Equity:</b>        ${equity:,.2f}\n"
        f"<b>Session:</b>       {_session()}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔱 HYDRA-S3  ·  24/7 LIVE  ·  v5.0"
    )


# Backward-compat aliases used by app.py buttons
def fmt_inevitable(asset, score, regime, direction, opp_id,
                    world_state=None, latent_sum=0.0, equity=100000.0):
    return fmt_s3_convergence(
        asset=asset, opp_id=opp_id, score=score, status="INEVITABLE",
        regime=regime, direction=direction, trigger_type="MANUAL_FIRE",
        world_state=world_state, latent_sum=latent_sum, equity=equity,
    )


def fmt_high_conviction(asset, score, regime, direction,
                         world_state=None, latent_sum=0.0, equity=100000.0):
    return fmt_s3_convergence(
        asset=asset, opp_id=f"{asset}-HC-MANUAL", score=score,
        status="HIGH CONVICTION", regime=regime, direction=direction,
        trigger_type="MANUAL_FIRE", world_state=world_state,
        latent_sum=latent_sum, equity=equity,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  SMART DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════

async def dispatch_opportunity_alert(
    asset: str, score: float, regime: str, direction: int,
    status: str, opp_id: str, trigger_type: str = "NEW_SIGNAL",
    world_state: dict = None, latent_sum: float = 0.0, equity: float = 100000.0,
):
    """
    Dispatch the correct alert type.
    - INEVITABLE      → always send (dedup by opp_id)
    - HIGH CONVICTION → 5-min cooldown per asset
    """
    global _sent_ids, _last_high_conv
    ws = world_state or {}

    msg = fmt_s3_convergence(
        asset=asset, opp_id=opp_id, score=score, status=status,
        regime=regime, direction=direction, trigger_type=trigger_type,
        world_state=ws, latent_sum=latent_sum, equity=equity,
    )

    if status == "INEVITABLE":
        if opp_id in _sent_ids:
            return
        _sent_ids.add(opp_id)
        if len(_sent_ids) > 500:
            _sent_ids = set(list(_sent_ids)[-500:])
        await send_alert_async(msg)

    elif status == "HIGH CONVICTION":
        now  = time.time()
        last = _last_high_conv.get(asset, 0)
        if now - last < 300:
            return
        _last_high_conv[asset] = now
        await send_alert_async(msg)
