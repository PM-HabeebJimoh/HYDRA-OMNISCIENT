"""
HYDRA-S3  |  24/7 Live Engine Daemon  v5.1
Polls all 6 causal signals ONCE per cycle (shared across all assets).
Implements S3-Surgical-Trigger: new Opportunity ID generated on:
  - Direction change (e.g., LONG → SHORT)
  - Status escalation (e.g., NOISE → HIGH CONVICTION → INEVITABLE)
  - Score surge > 0.05 while in active signal (score ≥ 0.70)
Per-asset INITIAL_SIGNAL has a 10-minute cooldown to prevent alert spam.
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
POLL_SECONDS = 30    # 30s poll — matches Bloomberg/Reuters refresh cadence; slower = less microstructure noise
HEARTBEAT_N  = 20    # every 20 cycles = every 10 minutes at 30s poll

# ── OBI Exponential Moving Average ────────────────────────────────────────────
# Raw Kraken L2 OBI (even at 200 levels) fluctuates ±0.2–0.4 per 30s snapshot.
# EMA with α=0.20 provides ~5-cycle (~2.5 min) smoothing window, converting
# microstructure noise into a stable directional signal.
_OBI_EMA_ALPHA: float       = 0.20
_obi_ema_val:   float | None = None   # global EMA state across cycles

# ── Status Hysteresis Thresholds ───────────────────────────────────────────────
# Entry thresholds (score must REACH these to upgrade status):
#   NOISE → HIGH CONVICTION : score ≥ 0.80
#   HIGH CONVICTION → INEVITABLE : score ≥ 0.95
# Exit thresholds (score must DROP BELOW these to downgrade status):
#   INEVITABLE → HIGH CONVICTION : score < 0.90   (5-pt band)
#   HIGH CONVICTION → NOISE      : score < 0.74   (6-pt band)
# This prevents rapid NOISE↔HC flipping when OBI hovers near the 0.55 boundary.
_HC_EXIT_SCORE   = 0.74
_INEV_EXIT_SCORE = 0.90


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
        "signals_live":    0,
        "last_cycle_utc":  "",
        "cycle_count":     0,
    }

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                s = json.load(f)
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

_asset_prev:          dict = {}   # asset → {status, direction, score}
_initial_signal_last: dict = {}   # asset → epoch seconds of last INITIAL_SIGNAL alert
_hysteresis_status:   dict = {}   # asset → current hysteresis-gated status string

# Cooldown constants
_INITIAL_COOLDOWN_S  = 600   # 10 min between INITIAL_SIGNAL per asset
_HC_COOLDOWN_S       = 300   # 5 min between any HIGH CONVICTION alert (in dispatcher)

# Status rank map (used by trigger and hysteresis)
_STATUS_RANK = {'NOISE': 0, 'HIGH CONVICTION': 1, 'INEVITABLE': 2, 'DATA_GAP': -1}


def _apply_hysteresis(asset: str, raw_status: str, score: float) -> str:
    """
    Prevent rapid status bouncing by applying separate entry/exit thresholds.

    Entry thresholds (must REACH to upgrade):
      NOISE → HIGH CONVICTION : score ≥ 0.80
      HIGH CONVICTION → INEVITABLE : score ≥ 0.95

    Exit thresholds (must DROP BELOW to downgrade):
      INEVITABLE → HIGH CONVICTION : score < 0.90   (5-pt hysteresis band)
      HIGH CONVICTION → NOISE      : score < 0.74   (6-pt hysteresis band)

    Without hysteresis, OBI hovering near 0.55 (score ~0.79–0.81) causes
    NOISE↔HC flipping every cycle. The 6-point band absorbs that noise.
    """
    prev_hyst = _hysteresis_status.get(asset, 'NOISE')
    prev_rank = _STATUS_RANK.get(prev_hyst, 0)
    raw_rank  = _STATUS_RANK.get(raw_status, 0)

    if raw_rank > prev_rank:
        # Upgrade: raw_status has already passed the entry threshold in convergence.py
        result = raw_status
    elif raw_rank == prev_rank:
        result = prev_hyst
    else:
        # Potential downgrade — apply exit threshold
        if prev_hyst == 'INEVITABLE' and score >= _INEV_EXIT_SCORE:
            result = 'INEVITABLE'     # Hold INEVITABLE until score < 0.90
        elif prev_hyst == 'HIGH CONVICTION' and score >= _HC_EXIT_SCORE:
            result = 'HIGH CONVICTION' # Hold HC until score < 0.74
        else:
            result = raw_status        # Genuine downgrade confirmed

    _hysteresis_status[asset] = result
    return result


def _surgical_trigger(asset: str, score: float, status: str,
                       direction: int) -> tuple[bool, str]:
    """
    Returns (should_trigger: bool, reason: str).
    A new Opportunity ID is generated when:
      1. Status ESCALATES to a higher tier (NOISE→HC, HC→INEVITABLE, or NOISE→INEVITABLE)
      2. Direction changes (and new direction is not 0)
      3. Score surges > 0.08 while already active (score >= 0.70)  [raised from 0.05]
      4. Score first crosses 0.70 for this asset (INITIAL_SIGNAL, 10-min cooldown)
    """
    prev = _asset_prev.get(asset)

    # ── Below active threshold — update state only, no trigger ────────────────
    if score < 0.70:
        _asset_prev[asset] = {'status': status, 'direction': direction, 'score': score}
        return False, ""

    # ── First time crossing 0.70 for this asset ───────────────────────────────
    if prev is None or prev.get('score', 0) < 0.70:
        now = time.time()
        last_init = _initial_signal_last.get(asset, 0)
        if now - last_init < _INITIAL_COOLDOWN_S:
            _asset_prev[asset] = {'status': status, 'direction': direction, 'score': score}
            remaining = int(_INITIAL_COOLDOWN_S - (now - last_init))
            logger.debug(f"[{asset}] INITIAL_SIGNAL suppressed — cooldown {remaining}s remaining")
            return False, ""
        _initial_signal_last[asset] = now
        _asset_prev[asset] = {'status': status, 'direction': direction, 'score': score}
        return True, "INITIAL_SIGNAL"

    # ── Already above threshold — check for meaningful changes ────────────────
    reason = ""

    prev_rank = _STATUS_RANK.get(prev['status'], 0)
    curr_rank = _STATUS_RANK.get(status, 0)

    # Condition 1: Status escalated to a higher tier
    if curr_rank > prev_rank:
        reason = f"STATUS_ESCALATION [{prev['status']}→{status}]"

    # Condition 2: Direction changed (meaningful direction only)
    elif direction != prev['direction'] and direction != 0 and prev['direction'] != 0:
        reason = f"DIRECTION_CHANGE [{prev['direction']}→{direction}]"

    # Condition 3: Score surged > 0.08 (raised from 0.05 to reduce noise triggers)
    elif score > prev['score'] + 0.08:
        reason = f"SCORE_SURGE [{prev['score']:.4f}→{score:.4f}]"

    # Update tracked state
    _asset_prev[asset] = {'status': status, 'direction': direction, 'score': score}

    if reason:
        return True, reason
    return False, ""


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DAEMON LOOP
# ══════════════════════════════════════════════════════════════════════════════

async def live_daemon():
    global _obi_ema_val

    logger.info("Starting daemon event loop...")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║   HYDRA-S3 ENTERPRISE DAEMON v5.1  —  24/7 ACTIVATED    ║")
    logger.info("╠══════════════════════════════════════════════════════════╣")
    logger.info("║   S3-SURGICAL-TRIGGER ARMED                              ║")
    logger.info("║   Signals ONCE per cycle · OBI EMA-smoothed · 30s poll  ║")
    logger.info("║   INITIAL_SIGNAL cooldown: 10 min per asset              ║")
    logger.info("║   Status hysteresis: HC exits at <0.74 · INEV at <0.90  ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")

    engine = S3ConvergenceEngine()
    state  = load_state()

    try:
        await send_alert_async(fmt_startup(len(MONITORED_ASSETS)))
    except Exception as e:
        logger.warning(f"Startup alert failed (non-fatal): {e}")

    logger.info(f"Monitoring {len(MONITORED_ASSETS)} assets: {MONITORED_ASSETS}")
    logger.info(f"Poll: {POLL_SECONDS}s | Heartbeat: every {HEARTBEAT_N} cycles | OBI EMA α={_OBI_EMA_ALPHA}")

    cycle = state.get('cycle_count', 0)

    while True:
        cycle_start = time.monotonic()
        cycle += 1

        # ── Heartbeat write (proves daemon is alive to UI freshness check) ────
        state['cycle_count']    = cycle
        state['last_cycle_utc'] = datetime.now(timezone.utc).isoformat()
        save_state(state)

        world_state = {}

        try:
            async with S3CausalCollector() as collector:

                # ── Fetch all 6 signals ONCE per cycle (shared across assets) ──
                try:
                    world_state = await collector.collect_all_parallel(
                        obi_symbol='XBTUSD'  # Kraken BTC/USD (200-level deep book)
                    )
                except Exception as collect_err:
                    logger.error(f"Collector error: {collect_err}")
                    world_state = {k: None for k in
                                   ['NASA', 'EIA', 'OpenAQ', 'ETH', 'RealYield', 'OBI']}

                # ── OBI Exponential Moving Average ────────────────────────────
                # Raw OBI from a single L2 snapshot is noisy (±0.3 per cycle).
                # EMA(α=0.20) smooths over ~5 cycles (~2.5 min) for stable scoring.
                # raw_obi is stored in last_signals for display; ema_obi is used for scoring.
                raw_obi = world_state.get('OBI')
                if raw_obi is not None:
                    if _obi_ema_val is None:
                        _obi_ema_val = raw_obi
                    else:
                        _obi_ema_val = (_OBI_EMA_ALPHA * raw_obi +
                                        (1.0 - _OBI_EMA_ALPHA) * _obi_ema_val)
                    logger.debug(f"OBI raw={raw_obi:+.4f}  EMA={_obi_ema_val:+.4f}")

                # Build smoothed world state for convergence evaluation
                world_state_eval = {**world_state}
                if _obi_ema_val is not None:
                    world_state_eval['OBI'] = _obi_ema_val

                # ── Update API health map ─────────────────────────────────────
                for sig, val in world_state.items():
                    state['api_health'][sig] = "ONLINE" if val is not None else "GAP"

                live_ct = sum(1 for v in world_state.values() if v is not None)

                # ── Per-asset evaluation (all share the same world state) ──────
                for asset in MONITORED_ASSETS:
                    try:
                        # Evaluate with EMA-smoothed OBI
                        report    = engine.evaluate(world_state_eval)
                        score     = report['score']
                        raw_status = report['status']
                        regime    = report['regime_name']
                        direction = report['direction']
                        lat_sum   = report.get('latent_sum', 0.0)

                        # ── Apply status hysteresis to prevent NOISE↔HC bouncing ──
                        status = _apply_hysteresis(asset, raw_status, score)

                        # ── History entry (includes direction for UI rendering) ─
                        state['history'][asset].append({
                            "time":      datetime.utcnow().isoformat(),
                            "score":     round(score, 6),
                            "status":    status,
                            "regime":    regime,
                            "direction": direction,
                            "obi_raw":   round(raw_obi, 4) if raw_obi is not None else None,
                            "obi_ema":   round(_obi_ema_val, 4) if _obi_ema_val is not None else None,
                        })
                        if len(state['history'][asset]) > 10_000:
                            state['history'][asset] = state['history'][asset][-10_000:]

                        obi_log = _obi_ema_val if _obi_ema_val is not None else world_state_eval.get('OBI', 'n/a')
                        logger.info(
                            f"[{asset:7s}] score={score:.4f} | {status:16s} | "
                            f"{regime:11s} | signals={live_ct}/6 | "
                            f"OBI_ema={obi_log!r:.6} RY={world_state.get('RealYield', 'n/a')!r}"
                        )

                        # ── S3-Surgical-Trigger ──────────────────────────────
                        should_fire, trigger_reason = _surgical_trigger(
                            asset, score, status, direction
                        )

                        if should_fire and score >= 0.70:
                            ts_str = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]
                            trigger_code = trigger_reason[:3].replace('[','').replace(']','')
                            opp_id = f"{asset}-{ts_str}-{trigger_code}"

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
                                f"score={score:.4f} | {status} | dir={direction} | ID={opp_id}"
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
            state['last_signals']  = world_state      # raw signals for display
            state['obi_ema']       = round(_obi_ema_val, 4) if _obi_ema_val is not None else None
            state['signals_live']  = sum(1 for v in world_state.values() if v is not None)

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
            live_sigs = sum(1 for v in world_state.values() if v is not None)
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
