# AGBA METTA MODEL — AUDUSD + GBPUSD + USDCAD — July 2026 — Daily / 4H / 1H

## Data gathered for this run

1H OHLC for **GBPUSD** and **USDCAD** did not exist in this repo. Fetched from
Investing.com (`tvc4`, `resolution=60`), day by day, and transcribed:

| pair | 1H bars | days | range | envelope_fixes |
|---|---:|---:|---|---:|
| GBPUSD | 312 | 16 | 2026-07-01 → 2026-07-23 | **0** |
| USDCAD | 312 | 16 | 2026-07-01 → 2026-07-23 | **0** |

Verification: aggregated each day's 1H bars and compared the high/low envelope
against the **independently fetched daily OHLC**. 12 of 13 full days consistent
for each pair; the single exception on each (GBPUSD 07-06, USDCAD 07-20) differs
by ~3 pips, which is a session-boundary effect, not a transcription error.

AUDUSD 1H came from the existing verified panel. Its feed ends 2026-07-27, and
after intersecting all three assets the usable 1H window is **2026-07-01 →
2026-07-23, 292 bars**. 4H resampled from those. Daily uses the full month.

## Results

Risk 20% | Leverage 500x | Hard stop 1% | Capital $100,000

| TF | timing | signals | days | bar_WR | asset_WR | stops | return | maxDD | final equity |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DAILY | SIGNAL-BAR | 4 | 4 | 100.0% | 100.0% | 0 | **+131.81%** | 0.00% | $231,809 |
| DAILY | **LIVE** | 4 | 4 | 0.0% | 25.0% | 1 | **−46.73%** | −46.73% | $53,267 |
| 4H | SIGNAL-BAR | 6 | 5 | 100.0% | 100.0% | 0 | **+49.73%** | 0.00% | $149,735 |
| 4H | **LIVE** | 6 | 5 | 50.0% | 44.4% | 0 | **−8.18%** | −14.62% | $91,819 |
| 1H | SIGNAL-BAR | 13 | 9 | 100.0% | 100.0% | 0 | **+69.23%** | 0.00% | $169,235 |
| 1H | **LIVE** | 13 | 9 | 53.8% | 41.0% | 0 | **−9.81%** | −15.14% | $90,193 |

## What this shows

**All three timeframes lose money under live-correct timing.** Daily is worst at
−46.73%; 4H and 1H lose roughly 8–10%.

The signal-bar column again shows **100% bar win rate, 100% asset win rate, zero
stops and 0.00% drawdown on every timeframe** — the fingerprint of entering a bar
whose close has already been read. Moving entry to the next bar's open turns
+131.81% / +49.73% / +69.23% into −46.73% / −8.18% / −9.81%.

**Intraday is less bad than daily here.** The single daily stop-out did the
damage: AUDUSD 07-13 → 07-14 entered 0.69180 and stopped at 0.69872 for −1.000%
(−$32,467). On 4H and 1H no stop was hit at all, and losses stayed in the
single digits. Smaller bars mean the 1% stop sits further away in relative terms
than a full day's range.

**USDCAD contributes almost nothing.** Its per-trade moves are ±0.01–0.13% while
AUDUSD and GBPUSD move several times that. At a flat 500x the basket's result is
effectively AUD and GBP.

## Sample-size caveat

4 daily signals, 6 on 4H, 13 on 1H. These are far too few to rank a basket. The
1H/4H window is also 17 sessions, not the full month, because the AUDUSD feed
stops on 07-27 and GBPUSD/USDCAD 1H were transcribed through 07-23.

Data: `data/raw/intraday_x/{GBPUSD,USDCAD}_2026jul_1h.json`
Trade logs: `backtest_results/live_model/july2026_audgbpcad_all_tf.json`
Reproduce: `python3 -m research.july_audgbpcad_all_tf`
