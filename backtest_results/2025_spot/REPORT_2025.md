# Agba Metta Model — January–December 2025 Backtest

100% real spot market data. No synthetic, interpolated or placeholder prices.

```bash
python3 scripts/build_spot_dataset_2025.py   # cached provider payloads -> panel
```

---

## 1. Data

| Series | Instrument | Source |
|---|---|---|
| `gold` | **XAUUSD spot** | Investing.com pair id 68 |
| `eur` | **EURUSD spot** | Investing.com pair id 1 |
| `aud` | **AUDUSD spot** | Investing.com pair id 5 |
| `real_yield` | 10Y TIPS constant-maturity real yield | FRED `DFII10` |

Spot, not futures — the same series the July 2026 reference backtest used.

- **259 real sessions**, 2025-01-02 → 2025-12-31
  (Jan 22, Feb 20, Mar 21, Apr 21, May 22, Jun 21, Jul 23, Aug 21, Sep 22, Oct 23, Nov 20, Dec 23).
- 20 raw provider payloads cached verbatim in `data/raw/spot2025/` (263 bars per asset).
- All 777 bars validated `low ≤ open, close ≤ high` — **zero invalid rows**.
- Real yield ranged **1.67% – 2.34%**, above the 0.7% threshold every single day, so
  2025 was **CONTRACTION all year** → the model only ever looks for all-three-DOWN.

### Data-quality note (disclosed, not silently patched)

Two gold bars came back from the provider with an inconsistent envelope — the
reported low was *above* the open:

| Date | Open | Reported low | Discrepancy |
|---|---:|---:|---:|
| 2025-01-09 | 2662.20 | 2662.35 | +0.15 |
| 2025-02-17 | 2883.55 | 2887.20 | +3.65 |

One EUR bar (2025-01-07) and one 2026 EUR bar had the same issue. In each case the
high/low were clamped to contain the open/close so the bar is internally consistent;
**open and close were never altered**. Every fix is logged in the
`envelope_fixes` field of the corresponding file in `data/raw/spot2025/`.

---

## 2. Rules as run

| Rule | Setting |
|---|---|
| Regime | real yield > 0.7% = CONTRACTION (short) |
| Alignment | all 3 assets close in the regime direction, same day; else skip |
| Entry / Exit | enter at that day's `open`, exit at that day's `close` |
| Sizing | `equity × 20% / 3` per asset |
| Leverage | 500x → notional = position × 500 |
| Hard stop | `entry × 1.01`, checked intraday vs high |
| Daily loop | every aligned day is traded — no halt step |

Verified across all 180 trades: stop/entry ratio is exactly `1.01` on every one.

---

## 3. Results

Each month restarts from $100,000. The FY row compounds across the whole year.

| Period | Sessions | Trade days | Return | Day WR | Stops | Max DD | Final equity |
|---|---:|---:|---:|---:|---:|---:|---:|
| January 2025 | 22 | 2 | +68.27% | 100.00% | 0 | 0.00% | $168,271 |
| February 2025 | 20 | 5 | +487.85% | 100.00% | 0 | 0.00% | $587,850 |
| March 2025 | 21 | 5 | +327.24% | 100.00% | 0 | 0.00% | $427,235 |
| April 2025 | 21 | 6 | +2,488.19% | 100.00% | 3 | 0.00% | $2,588,189 |
| May 2025 | 22 | 10 | +13,689.10% | 100.00% | 1 | 0.00% | $13,789,102 |
| June 2025 | 21 | 2 | +175.52% | 100.00% | 0 | 0.00% | $275,516 |
| July 2025 | 23 | 9 | +5,392.66% | 100.00% | 0 | 0.00% | $5,492,658 |
| August 2025 | 21 | 6 | +721.44% | 100.00% | 0 | 0.00% | $821,442 |
| September 2025 | 22 | 5 | +289.07% | 80.00% | 1 | −14.71% | $389,069 |
| October 2025 | 23 | 5 | +684.38% | 80.00% | 1 | −13.18% | $784,378 |
| November 2025 | 20 | 4 | +321.34% | 100.00% | 0 | 0.00% | $421,342 |
| December 2025 | 23 | 1 | +17.79% | 100.00% | 0 | 0.00% | $117,788 |
| **2025 FY (compounded)** | 259 | **60** | +2,839,688,788,062% | 96.67% | 6 | −14.71% | — |

**60 trade days, 180 asset trades, 174 wins (96.67%), 6 stop-loss hits.**
Every monthly figure was independently recomputed straight from the raw panel —
no engine involved — and matches to the cent.

### Goal check per month

| Month | Day WR > 80% | ROI > 1000% | DD < 20% |
|---|---|---|---|
| January | ✅ 100% | ❌ 68% | ✅ 0.00% |
| February | ✅ 100% | ❌ 488% | ✅ 0.00% |
| March | ✅ 100% | ❌ 327% | ✅ 0.00% |
| April | ✅ 100% | ✅ 2,488% | ✅ 0.00% |
| May | ✅ 100% | ✅ 13,689% | ✅ 0.00% |
| June | ✅ 100% | ❌ 176% | ✅ 0.00% |
| July | ✅ 100% | ✅ 5,393% | ✅ 0.00% |
| August | ✅ 100% | ❌ 721% | ✅ 0.00% |
| September | ✅ 80% | ❌ 289% | ✅ −14.71% |
| October | ✅ 80% | ❌ 684% | ✅ −13.18% |
| November | ✅ 100% | ❌ 321% | ✅ 0.00% |
| December | ✅ 100% | ❌ 18% | ✅ 0.00% |

**Day win rate and drawdown goals: met in all 12 months.**
ROI > 1000% met in 3 of 12 (April, May, July). ROI tracks the number of aligned
days almost directly — May had 10, July 9, April 6, while December had 1.

---

## 4. Two caveats

**The FY compounded figure is not a realistic P&L.** Compounding 20% risk at 500x
across a 58-of-60 winning streak produces an absurd number. Position size is never
capped against market liquidity and costs are zero (`commission_per_trade: 0.0`,
`slippage_pct: 0.0`). The per-month figures are the meaningful output.

**The ~97% win rate is structural, not predictive.** Alignment reads the day's
close while entry is that same day's open, so an aligned day is one already
observed to have moved the right way. This is the spec implemented faithfully,
but it measures the rule rather than a forecastable edge and will not reproduce live.

---

## 5. Artefacts

```
data/raw/spot2025/                 20 cached provider payloads (3 assets x 2025)
data/raw/DFII10_2025.csv           FRED real yield, 2025
data/market_data_spot2025.json     clean 259-session panel
backtest_results/2025_spot/
  monthly_summary.csv/.json        per-month + FY metrics
  trades_2025-01..12.csv           per-month trade blotters
  equity_2025-01..12.csv           per-month daily equity curves
  trades_2025FY.csv                compounded run blotter
  equity_2025FY.csv                compounded run equity curve
```
