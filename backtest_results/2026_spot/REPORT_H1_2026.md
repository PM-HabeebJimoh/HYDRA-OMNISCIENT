# Agba Metta Model — January–June 2026 Backtest

100% real spot market data. No synthetic, interpolated or placeholder prices.

```bash
python3 scripts/build_spot_dataset.py     # cached provider payloads -> panel
python3 scripts/run_monthly_backtest.py   # month-by-month backtest
```

---

## 1. Engine validated against the July 2026 benchmark

Before running Jan–Jun, the engine was replayed against the reference July 2026
backtest. It reproduces every published metric:

| Metric | Reference | Engine |
|---|---:|---:|
| Trade days | 4 | 4 ✓ |
| Final equity | $1,126,408 | $1,126,407.83 ✓ |
| ROI | +1,026.41% | +1,026.41% ✓ |
| Asset win rate | 12/12 | 12/12 ✓ |
| Stop-loss hits | 0 | 0 ✓ |
| Max drawdown | 0.00% | 0.00% ✓ |

All 12 July trades match line-by-line on entry, 1% stop and PnL — e.g.
Jul 7 XAU entry 4166.99 / stop 4208.66 / +1.43%, Jul 13 XAU stop 4138.59 / +2.36%,
Jul 23 XAU stop 4158.81 / +1.65%.

---

## 2. Data

| Series | Instrument | Source |
|---|---|---|
| `gold` | **XAUUSD spot** | Investing.com pair id 68 |
| `eur` | **EURUSD spot** | Investing.com pair id 1 |
| `aud` | **AUDUSD spot** | Investing.com pair id 5 |
| `real_yield` | 10Y TIPS constant-maturity real yield | FRED `DFII10` |

Spot — **not** futures. These are the same series the July reference used:
pair 68 returns `2026-07-07 gold 4166.99/4183.27/4092.02/4107.32` and pair 1
returns `EUR 1.1442/1.1449/1.1408/1.1412`, matching the reference exactly.

**128 real sessions**, 2026-01-02 → 2026-06-30 (Jan 21, Feb 20, Mar 22, Apr 22,
May 21, Jun 22). Raw provider payloads cached verbatim in `data/raw/spot/`;
`scripts/build_spot_dataset.py` only reshapes them. All 384 bars validated
`low ≤ open, close ≤ high` — zero invalid rows.

---

## 3. Rules as run

| Rule | Setting |
|---|---|
| Regime | real yield > 0.7% = CONTRACTION (short); < −0.1% = EXPANSION (long); else skip |
| Alignment | all 3 assets close in the regime direction, same day; else skip |
| Entry / Exit | enter at that day's `open`, exit at that day's `close` |
| Sizing | `equity × 20% / 3` per asset |
| Leverage | 500x → notional = position × 500 |
| Hard stop | `entry × 1.01` (SHORT), checked intraday vs high |
| Daily loop | every aligned day is traded — no halt step |

Verified in output: **all 111 trades** have stop/entry ratio exactly `1.01`.

---

## 4. Results

Each month restarts from $100,000. The H1 row compounds across the half-year.

| Period | Sessions | Trade days | Return | Day WR | Max DD | Final equity |
|---|---:|---:|---:|---:|---:|---:|
| January 2026 | 21 | 4 | +221.17% | 100.00% | 0.00% | $321,172 |
| February 2026 | 20 | 4 | +197.41% | 75.00% | 0.00% | $297,407 |
| March 2026 | 22 | 7 | +9,721.27% | 100.00% | 0.00% | $9,821,266 |
| April 2026 | 22 | 6 | +1,139.81% | 83.33% | −24.06% | $1,239,813 |
| May 2026 | 21 | 9 | +5,120.39% | 88.89% | −13.63% | $5,220,385 |
| June 2026 | 22 | 7 | +10,060.92% | 100.00% | 0.00% | $10,160,917 |
| **2026 H1 (compounded)** | 128 | **37** | +6,169,473,976.96% | 91.89% | −24.06% | $6.17tn |

**37 trade days, 111 asset trades, 8 stop-loss hits.**
Every monthly figure was independently recomputed straight from the raw spot
panel — no engine involved — and matches to the cent.

### Goal check per month

| Month | Day WR > 80% | ROI > 1000% | DD < 20% |
|---|---|---|---|
| January | ✅ 100% | ❌ 221% | ✅ 0.00% |
| February | ❌ 75% | ❌ 197% | ✅ 0.00% |
| March | ✅ 100% | ✅ 9,721% | ✅ 0.00% |
| April | ✅ 83.33% | ✅ 1,140% | ❌ −24.06% |
| May | ✅ 88.89% | ✅ 5,120% | ✅ −13.63% |
| June | ✅ 100% | ✅ 10,061% | ✅ 0.00% |

Four of six months clear all three goals. January and February miss on ROI —
quieter months with only 4 aligned days each and smaller per-trade moves.
April breaches the drawdown limit on a single stopped day.

---

## 5. Two caveats worth your attention

**The H1 compounded figure is not a realistic P&L.** $100k → $6.17 trillion is
arithmetically correct under the rules, but it compounds 20% risk at 500x across
a 34-of-37 winning streak. Position size is never capped against market liquidity,
and costs are zero (`commission_per_trade: 0.0`, `slippage_pct: 0.0`). Treat the
per-month figures as the meaningful output.

**The high win rates are structural.** Alignment reads the day's close while entry
is that same day's open, so an aligned day is one already observed to have moved
the right way. That is the spec as written and it is implemented faithfully — but
it means these months measure the rule, not a forecastable edge, and they will not
reproduce in live trading.

---

## 6. Artefacts

```
data/raw/spot/               18 cached provider payloads (3 assets x 6 months)
data/raw/DFII10.csv          FRED real yield
data/market_data_spot.json   clean 128-session panel
backtest_results/2026_spot/
  monthly_summary.csv/.json  per-month + H1 metrics
  trades_2026-01..06.csv     per-month trade blotters
  equity_2026-01..06.csv     per-month daily equity curves
  trades_2026H1.csv          compounded run blotter
  equity_2026H1.csv          compounded run equity curve
  JANUARY_2026.md            January deep-dive with full daily loop trace
```
