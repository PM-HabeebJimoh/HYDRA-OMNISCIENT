# Agba Metta Model — Live-Correct Backtest, February → June 2026

**Data:** 100% real Investing.com (tvc4 history endpoint). No synthetic bars, no interpolation, no approximations, no filled gaps. Every February 1H window was saved with `envelope_fixes = 0`. 4H is resampled from the real 1H bars into 00/04/08/12/16/20 UTC buckets.

**Timing (live-correct):** signal candle closes -> all 3 of XAUUSD/EURUSD/AUDUSD close UP = LONG, all 3 close DOWN = SHORT, mixed = skip -> **enter on the NEXT candle open** -> 1% stop from the *actual* entry price -> exit at that candle's close unless the stop hits intrabar.

**Sizing:** 20% of equity split across 3 assets. **V1** = 500x, no cap. **V3** = 400x with a -2% per-bar basket loss cap.

**Engine validation:** before accepting any February number, the engine was re-run on March 2026 and reproduced the previously published figures exactly (V1 Daily -92.97%, 4H -99.98%, 1H -99.75%; t = -0.33 / -0.47 / +0.32).

---

## 1. February 2026 data coverage

| Asset | 1H bars | Trading days |
|---|---:|---:|
| XAUUSD | 458 | 24 |
| EURUSD | 480 | 24 |
| AUDUSD | 480 | 24 |
| **Aligned (all 3 present)** | **458** | **24** |

All 20 February trading days (Feb 2-27) are present, plus Sunday-evening opens. 124 4H buckets, 20 daily sessions. **Total envelope violations across all 22 February files: 0.**

| Month | 1H bars | 4H buckets | Daily sessions |
|---|---:|---:|---:|
| February 2026 | 458 | 124 | 20 |
| March 2026 | 508 | 137 | 22 |
| April 2026 | 483 | 130 | 22 |
| May 2026 | 479 | 130 | 21 |
| June 2026 | 488 | 132 | 22 |

---

## 2. February 2026 results

| TF | Trades | Win rate | V1 (500x) | V1 max DD | V3 (400x, -2% cap) | V3 max DD | Stops |
|---|---:|---:|---:|---:|---:|---:|---:|
| Daily | 10 | 20.0% | -97.90% | -98.77% | 185.52% | -7.76% | 9 |
| 4H | 59 | 40.7% | -99.69% | -99.70% | 11,277.34% | -9.61% | 14 |
| 1H | 217 | 50.2% | -99.88% | -99.96% | 226,129.72% | -15.33% | 14 |

**February V1 loses 97.9% to 99.9% of capital on every single timeframe.** Raw edge: Daily t = -0.59, 4H t = -0.56, 1H t = -0.86 - all three negative.

---

## 3. All five months, side by side

| Month | TF | n | WR | V1 (500x) | V1 max DD | V3 (400x cap) | V3 max DD |
|---|---|---:|---:|---:|---:|---:|---:|
| February 2026 | Daily | 10 | 20.0% | -97.90% | -98.77% | 185.52% | -7.76% |
| February 2026 | 4H | 59 | 40.7% | -99.69% | -99.70% | 11,277.34% | -9.61% |
| February 2026 | 1H | 217 | 50.2% | -99.88% | -99.96% | 226,129.72% | -15.33% |
| March 2026 | Daily | 10 | 40.0% | -92.97% | -96.86% | 285.14% | -7.76% |
| March 2026 | 4H | 79 | 44.3% | -99.98% | -100.00% | 52,329.45% | -8.53% |
| March 2026 | 1H | 265 | 49.4% | -99.75% | -99.96% | 70,174,712.14% | -14.54% |
| April 2026 | Daily | 14 | 42.9% | -91.56% | -95.88% | 561.49% | -9.61% |
| April 2026 | 4H | 84 | 51.2% | -96.69% | -98.02% | 41,887.16% | -5.88% |
| April 2026 | 1H | 271 | 44.6% | -99.84% | -99.94% | 162,751.79% | -19.53% |
| May 2026 | Daily | 17 | 29.4% | -99.82% | -99.87% | 351.61% | -11.42% |
| May 2026 | 4H | 67 | 53.7% | 865.99% | -75.67% | 26,386.83% | -8.73% |
| May 2026 | 1H | 246 | 48.8% | -92.68% | -99.28% | 44,175.98% | -15.01% |
| June 2026 | Daily | 12 | 16.7% | -99.87% | -99.87% | 75.37% | -13.19% |
| June 2026 | 4H | 65 | 55.4% | -99.99% | -100.00% | 3,452.33% | -7.75% |
| June 2026 | 1H | 261 | 52.1% | -91.90% | -98.46% | 579,409.27% | -17.37% |

V1 is destroyed in **14 of 15** month/timeframe cells. The lone exception is May 4H (+865.99%), which draws down -75.67% getting there.

---

## 4. Raw edge and 15-test Bonferroni

Leverage and caps do not create edge. Stripping both out, the mean per-trade return is the only honest test.

| Month | TF | n | WR | Mean / trade | t | p (two-sided) |
|---|---|---:|---:|---:|---:|---:|
| February 2026 | Daily | 10 | 20.0% | -0.1260% | -0.59 | 0.5727 |
| February 2026 | 4H | 59 | 40.7% | -0.0274% | -0.56 | 0.5765 |
| February 2026 | 1H | 217 | 50.2% | -0.0114% | -0.86 | 0.3928 |
| March 2026 | Daily | 10 | 40.0% | -0.0636% | -0.33 | 0.7511 |
| March 2026 | 4H | 79 | 44.3% | -0.0214% | -0.47 | 0.6432 |
| March 2026 | 1H | 265 | 49.4% | +0.0046% | +0.32 | 0.7483 |
| April 2026 | Daily | 14 | 42.9% | +0.0046% | +0.03 | 0.9761 |
| April 2026 | 4H | 84 | 51.2% | +0.0093% | +0.26 | 0.7975 |
| April 2026 | 1H | 271 | 44.6% | -0.0101% | -1.06 | 0.2920 |
| May 2026 | Daily | 17 | 29.4% | -0.1708% | -1.30 | 0.2122 |
| May 2026 | 4H | 67 | 53.7% | +0.0649% | +2.13 | 0.0371 ***** |
| May 2026 | 1H | 246 | 48.8% | -0.0014% | -0.17 | 0.8684 |
| June 2026 | Daily | 12 | 16.7% | -0.2608% | -1.79 | 0.1013 |
| June 2026 | 4H | 65 | 55.4% | -0.0350% | -0.94 | 0.3493 |
| June 2026 | 1H | 261 | 52.1% | +0.0048% | +0.50 | 0.6205 |

**Bonferroni over 15 tests:** alpha = 0.05/15 = **0.003333**.
Smallest p is **May 4H, p = 0.0371** - does **not** survive (11x too large).
Expected p<0.05 under pure noise = **0.75**. Observed = **1**.

Eleven of the fifteen t-stats are negative. This is not a strategy with a weak edge; it is a strategy with no edge.

---

## 5. May 4H: February adds a fourth nail

4H t-stat by month:

| Feb | Mar | Apr | May | Jun |
|---:|---:|---:|---:|---:|
| -0.56 | -0.47 | +0.26 | +2.13 | -0.94 |

May is a single spike in a run of otherwise negative months. It fails Bonferroni, it reverses on both sides, and it now has **two** negative months before it rather than one.

**Pooled February -> June:**

| Pooled TF | n | WR | Mean / trade | t | V1 (500x) | V1 max DD |
|---|---:|---:|---:|---:|---:|---:|
| 4H | 354 | 49.15% | -0.0013% | -0.07 | -100.00% | -100.00% |
| 1H | 1260 | 48.97% | -0.0024% | -0.48 | -100.00% | -100.00% |

Adding February pushes the pooled 1H sample to **n = 1260** and the t-stat **down** from -0.11 to **-0.48**. Pooled 4H drops from +0.20 to **-0.07**. More data makes the result worse, not better - the opposite of what a real edge does.

---

## 6. Random-direction control - February

Keep the exact bars where 3-asset alignment fires, then coin-flip the side. 200 runs, seed 7. If the model has edge it must beat the coin flip.

| Test | Actual | Random median | Random runs beating actual |
|---|---:|---:|---:|
| 1H_V1_500x | -99.88% | -99.23% | 150/200 |
| 1H_V3_400x_cap2 | 226,129.72% | 489,942.26% | 149/200 |
| 4H_V1_500x | -99.69% | -98.37% | 145/200 |
| 4H_V3_400x_cap2 | 11,277.34% | 20,120.41% | 138/200 |

**In all four February controls the coin flip beat the model more often than not (138-150 of 200).** Random-side trading on the same bars produced a *better* median than the actual signal in every case.

---

## 7. V3 is the -2% cap, not the model

V3's large numbers come from truncating every loss at -2% while wins compound at 400x. Coin-flip directions on the same bars produce the same magnitude or larger:

| Cell | Model | Coin-flip median | Verdict |
|---|---:|---:|---|
| Feb 1H V3 | +226,130% | **+489,942%** | random ~2x better |
| Feb 4H V3 | +11,277% | **+20,120%** | random better |
| Apr 1H V3 | +145,474% | **+571,357%** | random ~4x better |
| Mar 4H V3 | +52,329% | **+118,680%** | random ~2x better |

Remove the cap and keep the identical signal (V1): -97.9% to -99.9% in February, and -91% to -100% in 14 of 15 cells overall. A cap is not an edge - and live, a -2% basket cap on a 400x position assumes you always fill at exactly -2% through gaps and news. You will not.

---

## 8. Goals vs. reality

| Goal | Target | Measured | Met? |
|---|---|---|---|
| Monthly ROI | > 700% | Feb V1: -97.90% / -99.69% / -99.88%. Across 15 cells only May 4H is positive. Pooled -100.00%. | **No** |
| Max drawdown | < 5% | Feb V1 DD -98.77% to -99.96%. | **No** |
| Live risk | < 7% | 20% of equity at 500x = 100x notional; a 1% adverse move is the account. | **No** |

---

## 9. Bottom line

Five consecutive months of 100% real Investing.com data, three timeframes, 15 independent tests, **1,260 pooled 1H trades** and 354 pooled 4H trades:

- February is negative on **all three** timeframes (t = -0.59, -0.56, -0.86) and V1 loses ~98-100% on each.
- Pooled 1H t = **-0.48**; pooled 4H t = **-0.07**. Adding February moved both *further from* significance.
- In every February control the coin flip beat the model.
- The stated goals are **not achievable** with this model under honest live timing.

The original +1,026% headline came from entering on the same candle whose close created the signal - look-ahead. You cannot trade a signal before it exists. With entry moved to the next candle open, as live trading requires, the edge is gone.

**Note on Apr/Jun figures:** loading all five months as one continuous panel lets the last candle of the prior month legitimately signal the first entry of the next - which is what a live trader sees. This adds one real trade to April and one to June versus the earlier isolated single-month runs (Apr 4H t +0.33 -> +0.26, Jun 4H t -1.02 -> -0.94). March is unchanged. Conclusions are unaffected.

---

*Raw results: `backtest_results/live_model/feb_to_june_2026_live_all_tf.json`. Engine: `scripts/agba_metta_live.py`, `scripts/intraday_engine.py`. Raw price windows: `data/raw/intraday/*2026feb*`.*
