---
name: OBI Stability Fix
description: Root cause and fix for NOISE↔HC status bouncing every 10s in the HYDRA-S3 daemon
---

## The Problem
Raw Kraken BTC/USD L2 OBI (even at 200 levels) oscillates ±0.2–0.5 per snapshot.
With a 10-second poll and direct score mapping, the score swings from 0.51 to 0.83
in consecutive cycles, causing NOISE↔HIGH CONVICTION flipping every cycle.

## Fixes Applied (all three required together)

### 1. Deeper OBI book — collector.py
`count=25` → `count=200` in Kraken Depth API URL.
More levels = more cumulative volume = more stable ratio.

### 2. OBI EMA smoothing — live_engine.py
Global `_obi_ema_val` with `_OBI_EMA_ALPHA = 0.20` (~5-cycle, ~2.5 min window).
`world_state_eval['OBI'] = _obi_ema_val` passed to engine; raw OBI still in `last_signals` for display.

### 3. Status hysteresis — live_engine.py `_apply_hysteresis()`
Separate entry vs exit thresholds:
- HC entry ≥ 0.80, HC exit < 0.74  (6-point band)
- INEVITABLE entry ≥ 0.95, INEVITABLE exit < 0.90  (5-point band)
`_hysteresis_status` dict tracks per-asset gated status.

### 4. Slower poll
`POLL_SECONDS`: 10 → 30 (Bloomberg/Reuters cadence; less microstructure noise)

### 5. Stricter SCORE_SURGE
+0.05 → +0.08 threshold to suppress noisy SCORE_SURGE triggers.

**Why:** Without all five, OBI microstructure noise propagates directly to status, making the terminal look broken (INEVITABLE one moment, NOISE the next).

**How to apply:** If instability returns, check (a) EMA alpha is ≤ 0.20, (b) hysteresis thresholds are intact, (c) Kraken count=200, (d) POLL_SECONDS=30.
