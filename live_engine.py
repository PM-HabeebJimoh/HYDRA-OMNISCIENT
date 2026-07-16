"""
HYDRA-S3  |  24/7 Live Engine Daemon  v5.0
Polls all 6 causal signals every 10 seconds.
Implements S3-Surgical-Trigger: new Opportunity ID generated on:
  - Direction change (e.g., LONG → SHORT)
  - Status escalation (e.g., HIGH CONVICTION → INEVITABLE)
  - Score surge > 0.05 while in active signal (score ≥ 0.70)
Auto-restarts on crash with 30-second delay.
State file written atomically every cycle for freshness monitoring.
"""
import asyncio
import logging
import json
import os
import time
from datetime import datetime, timezone

from core.collector   import S3CausalCollector
from core.convergence import S3ConvergenceEngine
from core.telegram_alerts import (
    send_alert_async, fmt_startup, fmt_heartbeat, dispatch_opportunity_alert,
)
from config import MONITORED_ASSETS, THRESHOLDS, SYMBOL_MAP

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler("system_audit.log", encoding='utf-8'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('HYDRA-S3-DAEMON')

STATE_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enterprise_state.json")
POLL_SECONDS = 10
HEARTBEAT_N  = 60    # every 60 cycles = every 10 minutes


# ══════════════════════════════════════════════════════════════════════════════
#  STATE I/O
# ══════════════════════════════════════════════════════════════════════════════

def _blank_state() -> dict:
    return {
        "equity":          100000.0,
        "initial_capital": 100000.0,
        "trades":          [],
        "opportunities":   [],
        "history":         {a: [] for a in MONITORED_ASSETS},
        "settings":        THRESHOLDS,
        "api_health":      {k: "Unknown" for k in ["NASA","EIA","OpenAQ","ETH","RealYield","OBI"]},
        "last_signals":    {},
        "last_cycle_utc":  "",
        "cycle_count":     0,
    }

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                s = json.load(f)
            # Ensure all keys present
            blank = _blank_state()
            for k, v in blank.items():
                if k not in s:
                    s[k] = v
            for asset in MONITORED_ASSETS:
                if asset not in s['history']:
                    s['history'][asset] = []
            return s
        except Exception as e:
            logger.error(f"State load error: {e} — starting blank")
    return _blank_state()

def save_state(state: dict):
    try:
        tmp = STATE_FILE + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        logger.error(f"State save error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  S3-SURGICAL-TRIGGER  —  Smart Opportunity ID generation
# ══════════════════════════════════════════════════════════════════════════════

_asset_prev: dict = {}   # asset → {status, direction, score}

def _surgical_trigger(asset: str, score: float, status: str,
                       direction: int) -> tuple[bool, str]:
    """
    Returns (should_trigger: bool, reason: str).
    A new Opportunity ID is generated when:
      1. Direction changes (and new direction is not 0)
      2. Status changes (escalation or downgrade when score >= 0.70)
      3. Score increases by > 0.05 while active (score >= 0.70)
    """
    prev = _asset_prev.get(asset)

    # Below threshold — update state, no trigger
    if score < 0.70:
        _asset_prev[asset] = {'status': status, 'direction': direction, 'score': score}
        return False, ""

    # First time above threshold for this asset
    if prev is None or prev.get('score', 0) < 0.70:
        _asset_prev[asset] = {'status': status, 'direction': direction, 'score': score}
        return True, "INITIAL_SIGNAL"

    reason = ""

    # Condition 1: Direction changed (and meaningful direction)
    if direction != prev['direction'] and direction != 0:
        reason = f"DIRECTION_CHANGE [{prev['direction']}→{direction}]"

    # Condition 2: Status changed
    elif status != prev['status']:
        reason = f"STATUS_CHANGE [{prev['status']}→{status}]"

    # Condition 3: Score surged > 0.05
    elif score > prev['score'] + 0.05:
        reason = f"SCORE_SURGE [{prev['score']:.4f}→{score:.4f}]"

    # Update prev state
    _asset_prev[asset] = {'status': status, 'direction': direction, 'score': score}

    if reason:
        return True, reason
    return False, ""


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DAEMON LOOP
# ══════════════════════════════════════════════════════════════════════════════

async def live_daemon():
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║   HYDRA-S3 ENTERPRISE DAEMON v5.0  —  24/7 ACTIVATED    ║")
    logger.info("╠══════════════════════════════════════════════════════════╣")
    logger.info("║   S3-SURGICAL-TRIGGER ARMED                              ║")
    logger.info("║   Triggers: direction change | status change | +0.05     ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")

    engine = S3ConvergenceEngine()
    state  = load_state()

    # Startup Telegram
    try:
        await send_alert_async(fmt_startup(len(MONITORED_ASSETS)))
    except Exception as e:
        logger.warning(f"Startup alert failed (non-fatal): {e}")

    logger.info(f"Monitoring {len(MONITORED_ASSETS)} assets: {MONITORED_ASSETS}")
    logger.info(f"Poll: {POLL_SECONDS}s | Heartbeat: every {HEARTBEAT_N} cycles")

    cycle = state.get('cycle_count', 0)

    while True:
        cycle_start = time.monotonic()
        cycle += 1

        # ── Heartbeat signal write (proves daemon is alive) ───────────────────
        state['cycle_count']    = cycle
        state['last_cycle_utc'] = datetime.now(timezone.utc).isoformat()
        save_state(state)   # early write so UI shows daemon is live immediately

        last_world_state = {}

        try:
            async with S3CausalCollector() as collector:

                for asset in MONITORED_ASSETS:
                    obi_sym = SYMBOL_MAP.get(asset, 'XAUUSDT')

                    try:
                        world_state = await collector.collect_all_parallel(
                            obi_symbol=obi_sym
                        )
                    except Exception as collect_err:
                        logger.error(f"Collector error for {asset}: {collect_err}")
                        world_state = {k: None for k in
                                       ['NASA','EIA','OpenAQ','ETH','RealYield','OBI']}

                    last_world_state = world_state

                    try:
                        report    = engine.evaluate(world_state)
                        score     = report['score']
                        status    = report['status']
                        regime    = report['regime_name']
                        direction = report['direction']
                        lat_sum   = report.get('latent_sum', 0.0)

                        # ── History ─────────────────────────────────────────────
                        state['history'][asset].append({
                            "time":   datetime.utcnow().isoformat(),
                            "score":  round(score, 6),
                            "status": status,
                            "regime": regime,
                        })
                        if len(state['history'][asset]) > 10_000:
                            state['history'][asset] = state['history'][asset][-10_000:]

                        # ── API health map ───────────────────────────────────────
                        for sig, val in world_state.items():
                            state['api_health'][sig] = "ONLINE" if val is not None else "GAP"

                        # ── Logging ──────────────────────────────────────────────
                        live_ct = sum(1 for v in world_state.values() if v is not None)
                        logger.info(
                            f"[{asset:7s}] score={score:.4f} | {status:16s} | "
                            f"{regime:11s} | signals={live_ct}/6 | "
                            f"OBI={world_state.get('OBI')} "
                            f"RY={world_state.get('RealYield')}"
                        )

                        # ── S3-Surgical-Trigger ──────────────────────────────────
                        should_fire, trigger_reason = _surgical_trigger(
                            asset, score, status, direction
                        )

                        if should_fire and score >= 0.70:
                            ts_str = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]
                            opp_id = f"{asset}-{ts_str}-{trigger_reason[:3].replace('[','').replace(']','')}"

                            opp = {
                                "id":                opp_id,
                                "asset":             asset,
                                "timestamp":         datetime.utcnow().isoformat(),
                                "score":             score,
                                "status":            status,
                                "regime":            regime,
                                "direction":         direction,
                                "trigger":           trigger_reason,
                                "manifold_snapshot": {
                                    k: v for k, v in world_state.items()
                                    if v is not None
                                },
                                "executed": False,
                                "trade_id": None,
                            }
                            state['opportunities'].append(opp)

                            logger.warning(
                                f"🔥 SURGICAL TRIGGER [{asset}] | {trigger_reason} | "
                                f"score={score:.4f} | {status} | ID={opp_id}"
                            )

                            try:
                                await dispatch_opportunity_alert(
                                    asset=asset, score=score, regime=regime,
                                    direction=direction, status=status,
                                    opp_id=opp_id, trigger_type=trigger_reason,
                                    world_state=world_state, latent_sum=lat_sum,
                                    equity=state['equity'],
                                )
                            except Exception as te:
                                logger.warning(f"Telegram dispatch error: {te}")

                    except Exception as eval_err:
                        logger.error(f"Eval error for {asset}: {eval_err}", exc_info=True)

            # ── End-of-cycle state updates ────────────────────────────────────
            state['opportunities'] = state['opportunities'][-2000:]
            state['last_signals']  = last_world_state

        except asyncio.CancelledError:
            logger.info("Daemon cancelled — saving state and exiting.")
            save_state(state)
            return
        except Exception as loop_err:
            logger.critical(f"Cycle {cycle} loop error: {loop_err}", exc_info=True)

        # ── Final atomic state write ──────────────────────────────────────────
        state['last_cycle_utc'] = datetime.now(timezone.utc).isoformat()
        save_state(state)

        # ── Heartbeat Telegram ────────────────────────────────────────────────
        if cycle % HEARTBEAT_N == 0:
            live_sigs = sum(1 for v in last_world_state.values() if v is not None)
            logger.info(f"♥ Heartbeat cycle={cycle} signals_live={live_sigs}/6")
            try:
                await send_alert_async(fmt_heartbeat(
                    cycle, len(MONITORED_ASSETS),
                    len(state['opportunities']),
                    equity=state['equity'],
                    signals_live=live_sigs,
                ))
            except Exception as he:
                logger.warning(f"Heartbeat alert error: {he}")

        # ── Poll interval ──────────────────────────────────────────────────────
        elapsed = time.monotonic() - cycle_start
        sleep_t = max(0.5, POLL_SECONDS - elapsed)
        await asyncio.sleep(sleep_t)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT — crash-recovery outer loop
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    restart_delay = 30

    while True:
        try:
            logger.info("Starting daemon event loop...")
            asyncio.run(live_daemon())
            logger.warning("Daemon exited normally — restarting in 5s.")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt — daemon stopped by operator.")
            break
        except Exception as fatal:
            logger.critical(
                f"Daemon fatal crash: {fatal} — restarting in {restart_delay}s...",
                exc_info=True
            )
            time.sleep(restart_delay)
