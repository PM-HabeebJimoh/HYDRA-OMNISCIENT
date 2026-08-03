# Agba Metta Model — Live-Correct Backtest, March → June 2026

**Data:** 100% real Investing.com (tvc4 history endpoint). No synthetic bars, no interpolation, no approximations. Every raw 1H window saved with `envelope_fixes = 0`. 4H is resampled from the real 1H bars into 00/04/08/12/16/20 UTC buckets.

**Timing (live-correct, per spec):** signal candle closes → all 3 of XAUUSD/EURUSD/AUDUSD close UP = LONG, all 3 close DOWN = SHORT, mixed = skip → **enter on the NEXT candle open** → 1% stop from the *actual* entry price → exit at that candle's close unless the stop hits intrabar.

**Sizing:** 20% of equity, split across 3 assets. **V1** = 500x, no cap. **V3** = 400x with a −2% per-bar basket loss cap.

---

## 1. Data coverage

| Month | 1H bars (all 3 assets aligned) | Trading days | 4H buckets | Daily sessions |
|---|---:|---:|---:|---:|
| March 2026 | 508 | 27 | 137 | 22 |
| April 2026 | 483 | 25 | 130 | 22 |
| May 2026 | 479 | 25 | 130 | 21 |
| June 2026 | 488 | 26 | 132 | 22 |

March 2026 is the most complete month in the set: 508 aligned 1H bars across 27 days, all 22 trading days present.

April 3, 2026 was **Good Friday** — gold returned 0 bars, EUR and AUD 21 bars each. Verified per-symbol; this is a genuine market closure, not a data gap. 3-asset alignment therefore cannot fire that day.

---

## 2. Headline results by month and timeframe

| Month | TF | Trades | Win rate | V1 (500x) return | V1 max DD | V3 (400x, −2% cap) return | V3 max DD | Stops |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| March 2026 | DAILY | 10 | 40.0% | -92.97% | -96.86% | 285.14% | -7.76% | 11 |
| March 2026 | 4H | 79 | 44.3% | -99.98% | -100.00% | 52,329.45% | -8.53% | 21 |
| March 2026 | 1H | 265 | 49.4% | -99.75% | -99.96% | 70,174,712.14% | -14.54% | 16 |
| April 2026 | DAILY | 14 | 42.9% | -91.56% | -95.88% | 561.49% | -9.61% | 7 |
| April 2026 | 4H | 83 | 51.8% | -95.79% | -97.47% | 42,744.04% | -5.88% | 9 |
| April 2026 | 1H | 270 | 44.4% | -99.86% | -99.94% | 145,473.63% | -19.53% | 3 |
| May 2026 | DAILY | 17 | 29.4% | -99.82% | -99.87% | 351.61% | -11.42% | 11 |
| May 2026 | 4H | 67 | 53.7% | 865.99% | -75.67% | 26,386.83% | -8.73% | 1 |
| May 2026 | 1H | 246 | 48.8% | -92.68% | -99.28% | 44,175.98% | -15.01% | 2 |
| June 2026 | DAILY | 12 | 16.7% | -99.87% | -99.87% | 75.37% | -13.19% | 10 |
| June 2026 | 4H | 64 | 54.7% | -99.99% | -100.00% | 3,001.34% | -7.75% | 11 |
| June 2026 | 1H | 260 | 52.3% | -91.72% | -98.46% | 589,802.48% | -17.37% | 6 |

**V1 — the model with no cap — loses 91% to 100% of capital in 11 of the 12 month/timeframe cells.** The single exception is May 4H (+865.99%), and it does so while drawing down −75.67% on the way. Nothing here is tradeable.

---

## 3. The raw edge (1x leverage, no cap, no compounding artifacts)

Leverage and caps do not create edge; they only scale and distort it. Stripping both out and measuring the mean per-trade return is the only honest test of whether the alignment signal predicts anything.

| Month | TF | n | Win rate | Mean return / trade | t-stat | p-value (two-sided) |
|---|---|---:|---:|---:|---:|---:|
| March 2026 | DAILY | 10 | 40.0% | -0.0636% | -0.33 | 0.7511 |
| March 2026 | 4H | 79 | 44.3% | -0.0214% | -0.47 | 0.6432 |
| March 2026 | 1H | 265 | 49.4% | +0.0046% | +0.32 | 0.7483 |
| April 2026 | DAILY | 14 | 42.9% | +0.0046% | +0.03 | 0.9761 |
| April 2026 | 4H | 83 | 51.8% | +0.0120% | +0.33 | 0.7429 |
| April 2026 | 1H | 270 | 44.4% | -0.0107% | -1.12 | 0.2658 |
| May 2026 | DAILY | 17 | 29.4% | -0.1708% | -1.30 | 0.2122 |
| May 2026 | 4H | 67 | 53.7% | +0.0649% | +2.13 | 0.0371 **\*** |
| May 2026 | 1H | 246 | 48.8% | -0.0014% | -0.17 | 0.8684 |
| June 2026 | DAILY | 12 | 16.7% | -0.2608% | -1.79 | 0.1013 |
| June 2026 | 4H | 64 | 54.7% | -0.0384% | -1.02 | 0.3106 |
| June 2026 | 1H | 260 | 52.3% | +0.0049% | +0.50 | 0.6144 |

**Bonferroni over 12 tests:** α = 0.05 / 12 = **0.004167**.
Smallest p-value is **May 4H, p = 0.0371** — it does **not** survive.
Expected number of p < 0.05 under pure noise across 12 tests = **0.6**. Observed = **1**.

One hit out of twelve is precisely what randomness delivers. There is no signal in this table.

---

## 4. May 4H is now dead three separate ways

May 4H (t = +2.13) was the only cell that ever looked like a real edge. Adding March kills it conclusively:

**(a) Multiple testing.** With 12 tests the threshold is α = 0.004167. May 4H's p = 0.0371 is 9× too large.

**(b) No persistence — it reverses in every adjacent month.** 4H t-stat by month:

| Mar | Apr | May | Jun |
|---:|---:|---:|---:|
| -0.47 | +0.33 | +2.13 | -1.02 |

A real edge does not appear for one month and vanish on both sides of it. This is the shape of a lucky month.

**(c) It disappears when pooled.** Combining all four months:

| Pooled TF | n | Win rate | Mean / trade | t-stat | V1 (500x) | V1 max DD |
|---|---:|---:|---:|---:|---:|---:|
| 4H | 295 | 50.85% | +0.0040% | +0.20 | -100.00% | -100.00% |
| 1H | 1043 | 48.71% | -0.0006% | -0.11 | -100.00% | -100.00% |

Pooled 1H has n = 1043 trades — a large sample — and the mean per-trade return is -0.0006%, t = -0.11. That is zero. Pooled V1 on both timeframes is a total wipeout.

---

## 5. Random-direction control

The old shuffle test was invalid — reordering trades in a multiplicative equity curve is order-invariant, so it always "passed." It was replaced with a proper control: **keep the exact bars where 3-asset alignment fires, then coin-flip the direction instead of using the model's signal. 200 runs, seed 7.** If the model has edge, it must beat the random-side version.

| Month | Test | Actual return | Random median | Random runs that BEAT actual (of 200) |
|---|---|---:|---:|---:|
| March 2026 | 1H_V1_500x | -99.75% | -99.88% | 89 |
| March 2026 | 1H_V3_400x_cap2 | 70,174,712.14% | 49,395,008.59% | 77 |
| March 2026 | 4H_V1_500x | -99.98% | -99.94% | 124 |
| March 2026 | 4H_V3_400x_cap2 | 52,329.45% | 118,679.71% | 139 |
| April 2026 | 1H_V1_500x | -99.86% | -97.25% | 174 |
| April 2026 | 1H_V3_400x_cap2 | 145,473.63% | 571,356.90% | 181 |
| April 2026 | 4H_V1_500x | -95.79% | -98.41% | 72 |
| April 2026 | 4H_V3_400x_cap2 | 42,744.04% | 30,392.65% | 75 |
| May 2026 | 1H_V1_500x | -92.68% | -89.73% | 109 |
| May 2026 | 1H_V3_400x_cap2 | 44,175.98% | 54,186.53% | 117 |
| May 2026 | 4H_V1_500x | 865.99% | -90.16% | 1 |
| May 2026 | 4H_V3_400x_cap2 | 26,386.83% | 6,012.57% | 4 |
| June 2026 | 1H_V1_500x | -91.72% | -97.25% | 72 |
| June 2026 | 1H_V3_400x_cap2 | 589,802.48% | 370,255.56% | 73 |
| June 2026 | 4H_V1_500x | -99.99% | -98.09% | 185 |
| June 2026 | 4H_V3_400x_cap2 | 3,001.34% | 9,460.75% | 172 |

Under the null, ~100 of 200 random runs should beat the actual. Across the 16 controls the counts scatter around 100 (72, 73, 75, 77, 89, 109, 117, 124, 139, 172, 174, 181, 185 …). The model direction is statistically indistinguishable from a coin flip.

The only outlier is **May 4H (1/200 and 4/200)** — the same cell already killed in section 4. One outlier out of 16 controls, in the month that fails Bonferroni and reverses on both sides, is noise.

---

## 6. V3's huge numbers are a cap artifact, not edge

V3 posts returns like +70,174,712% (March 1H). That is not the model working. The −2% per-bar basket cap truncates every loss at −2% while wins compound at 400x. **Any** sequence of trades with roughly 50/50 outcomes will explode under that asymmetry. The proof is the random-direction control: coin-flip directions on the same bars produce the same order of magnitude, and often *more*.

| Cell | Model (actual) | Coin-flip median | Verdict |
|---|---:|---:|---|
| Mar 1H V3 | +70,174,712% | +49,395,009% | same order |
| Apr 1H V3 | +145,474% | **+571,357%** | random did ~4× better |
| Mar 4H V3 | +52,329% | **+118,680%** | random did ~2× better |
| May 1H V3 | +44,176% | +54,187% | random better |
| Jun 1H V3 | +589,802% | +370,256% | same order |

Same signal, cap removed (V1): −91% to −100% in almost every cell. The cap is doing all the work, and a cap is not an edge — in live trading a −2% basket cap means you must be able to exit at exactly −2% on a 400x position, in a gap, every time. You cannot.

---

## 7. Stated goals vs. measured reality

| Goal | Target | Best honest result (V1, 500x) | Met? |
|---|---|---|---|
| Monthly ROI | > 700% | May 4H +865.99% — one cell out of 12; every other cell −91% to −100%; pooled −100.00% | **No** |
| Max drawdown | < 5% | V1 ranges −95.88% to −100.00%; the one profitable cell drew down −75.67% | **No** |
| Live risk | < 7% | 20% of equity at 500x = 100x notional exposure; a 1% adverse move is a full account | **No** |

V3's drawdowns (−5.88% to −19.53%) look closer to target, but they are the mechanical consequence of the −2% cap being assumed to always fill, not a property of the strategy.

---

## 8. Bottom line

Across **four consecutive months of 100% real Investing.com data**, three timeframes, 12 independent tests, 1,043 pooled 1H trades and 295 pooled 4H trades:

- The 3-asset alignment signal has **no measurable predictive edge**. Pooled 1H t = −0.11, pooled 4H t = +0.20.
- Every apparent win is explained by either the −2% cap artifact (V3) or single-month luck (May 4H), and both are ruled out by the controls.
- Without a cap, the model at 500x **destroys the account in 11 of 12 month/timeframe cells**.
- The stated goals — 700% monthly, <5% drawdown, <7% risk — are **not achievable** with this model under honest live timing.

The earlier headline result of +1,026% came from entering on the *same* candle whose close produced the signal. That is look-ahead: you cannot trade a signal before the signal exists. Once entry moves to the next candle open, as it must live, the edge is gone.

---

*Raw results: `backtest_results/live_model/mar_to_june_2026_live_all_tf.json`. Engine: `scripts/agba_metta_live.py`. Raw price windows: `data/raw/intraday/`.*
