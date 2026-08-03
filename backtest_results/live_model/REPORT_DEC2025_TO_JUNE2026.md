# Agba Metta Model - Live-Correct Backtest, December 2025 -> June 2026

**Data:** 100% real Investing.com (tvc4 history endpoint). No synthetic bars, no interpolation, no approximations, no filled gaps. Every December window saved with `envelope_fixes = 0`.

**Timing (live-correct):** signal candle closes -> all 3 of XAUUSD/EURUSD/AUDUSD close UP = LONG, all 3 close DOWN = SHORT, mixed = skip -> **enter on the NEXT candle open** -> 1% stop from the *actual* entry price -> exit at that candle's close unless stopped intrabar.

**Sizing:** 20% of equity split across 3 assets. **V1** = 500x, no cap. **V3** = 400x with a -2% per-bar basket loss cap.

## Christmas closure - verified, not assumed

The daily panel carries a `2025-12-25` bar. The raw 1H feed shows that is **not** a real trading session:

| Asset | Halts | Resumes | Bars on Dec 25 |
|---|---|---|---:|
| XAUUSD | Dec 24 18:00 UTC | Dec 25 23:00 UTC | 1 |
| EURUSD | Dec 24 21:00 UTC | Dec 25 22:00 UTC | 2 |
| AUDUSD | Dec 24 21:00 UTC | Dec 25 22:00 UTC | 2 |

Dec 25 is a **holiday stub** - one or two late-evening bars as the week reopens, not a full session. This was checked per-symbol in the real data rather than assumed from the calendar.

---

## 1. Coverage

| Month | 1H bars | 4H buckets | Daily sessions |
|---|---:|---:|---:|
| December 2025 | 481 | 131 | 23 |
| January 2026 | 480 | 131 | 22 |
| February 2026 | 458 | 124 | 20 |
| March 2026 | 508 | 137 | 22 |
| April 2026 | 483 | 130 | 22 |
| May 2026 | 479 | 130 | 21 |
| June 2026 | 488 | 132 | 22 |

December: XAUUSD 502 / EURUSD 505 / AUDUSD 505 bars; **481 aligned** across 27 days, all 23 trading days present.

---

## 2. December 2025 results

| TF | Trades | Win rate | V1 (500x) | V1 max DD | V3 (400x, -2% cap) | V3 max DD |
|---|---:|---:|---:|---:|---:|---:|
| Daily | 5 | 60.0% | 89.11% | -23.04% | 118.46% | -2.00% |
| 4H | 50 | 60.0% | 68.11% | -55.79% | 989.19% | -6.06% |
| 1H | 193 | 45.1% | -96.66% | -97.44% | 1,485.49% | -19.00% |

December is **mildly positive on Daily (+89.11%) and 4H (+68.11%)** and clearly negative on 1H (-96.66%).

Three things to be honest about:

**(a) The Daily sample is 5 trades.** Five. That is not a result, it is an anecdote. t = +1.08, p = 0.34.

**(b) Nothing is significant.** Dec Daily t = +1.08, 4H t = +0.99, 1H t = **-1.53**. None come close to Bonferroni at alpha = 0.002381.

**(c) The drawdowns are still disqualifying.** 4H returns +68% but draws down **-55.79%** on the way. Daily draws -23.04%. Both blow through the <5% goal.

---

## 3. All seven months

| Month | TF | n | WR | V1 (500x) | V1 max DD | V3 (400x cap) | V3 max DD |
|---|---|---:|---:|---:|---:|---:|---:|
| December 2025 | Daily | 5 | 60.0% | 89.11% | -23.04% | 118.46% | -2.00% |
| December 2025 | 4H | 50 | 60.0% | 68.11% | -55.79% | 989.19% | -6.06% |
| December 2025 | 1H | 193 | 45.1% | -96.66% | -97.44% | 1,485.49% | -19.00% |
| January 2026 | Daily | 10 | 60.0% | 733.97% | -82.32% | 2,350.52% | -7.76% |
| January 2026 | 4H | 57 | 61.4% | 446.76% | -83.10% | 28,794.86% | -5.88% |
| January 2026 | 1H | 201 | 47.8% | -97.86% | -98.87% | 161,077.02% | -14.47% |
| February 2026 | Daily | 10 | 20.0% | -97.90% | -98.77% | 185.52% | -7.76% |
| February 2026 | 4H | 60 | 40.0% | -99.79% | -99.80% | 11,049.79% | -9.61% |
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

V1 is destroyed in **16 of 21** month/timeframe cells.

---

## 4. Raw edge and 21-test Bonferroni

| Month | TF | n | WR | Mean / trade | t | p (two-sided) |
|---|---|---:|---:|---:|---:|---:|
| December 2025 | Daily | 5 | 60.0% | +0.1844% | +1.08 | 0.3393 |
| December 2025 | 4H | 50 | 60.0% | +0.0273% | +0.99 | 0.3280 |
| December 2025 | 1H | 193 | 45.1% | -0.0115% | -1.53 | 0.1267 |
| January 2026 | Daily | 10 | 60.0% | +0.4619% | +1.76 | 0.1120 |
| January 2026 | 4H | 57 | 61.4% | +0.0972% | +1.69 | 0.0958 |
| January 2026 | 1H | 201 | 47.8% | -0.0006% | -0.04 | 0.9669 |
| February 2026 | Daily | 10 | 20.0% | -0.1260% | -0.59 | 0.5727 |
| February 2026 | 4H | 60 | 40.0% | -0.0324% | -0.67 | 0.5039 |
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

**Bonferroni over 21 tests:** alpha = 0.05/21 = **0.002381**.
Smallest p is **May 4H, p = 0.0371** - does **not** survive (16x too large).
Expected p<0.05 under pure noise = **1.05**. Observed = **1**.

**Observed hits (1) is now BELOW what noise alone would produce (1.05).** After 21 independent tests on seven months of real data, the model has produced fewer significant results than random chance would.

---

## 5. The 4H seasonal pattern is a coin flip

4H t-stat by month:

| Dec | Jan | Feb | Mar | Apr | May | Jun |
|---:|---:|---:|---:|---:|---:|---:|
| +0.99 | +1.69 | -0.67 | -0.47 | +0.26 | +2.13 | -0.94 |

Positive, positive, negative, negative, positive, positive, negative. Dec-Jan look like a promising run until Feb-Mar erase it.

**Pooled December -> June (seven months):**

| Pooled TF | n | WR | Mean / trade | t | V1 (500x) | V1 max DD |
|---|---:|---:|---:|---:|---:|---:|
| 4H | 462 | 51.73% | +0.0133% | +0.84 | -100.00% | -100.00% |
| 1H | 1654 | 48.37% | -0.0033% | -0.77 | -100.00% | -100.00% |

Pooled 4H t = **+0.84** on n = 462. Pooled 1H t = **-0.77** on n = 1654. **Both pooled V1 curves end at -100.00%.**

---

## 6. Random-direction control - December

Keep the exact bars where 3-asset alignment fires, coin-flip the side, 200 runs, seed 7.

| Test | Actual | Random median | Random runs beating actual |
|---|---:|---:|---:|
| 1H_V1_500x | -96.66% | -60.59% | 188/200 |
| 1H_V3_400x_cap2 | 1,485.49% | 4,896.63% | 189/200 |
| 4H_V1_500x | 68.11% | -49.23% | 32/200 |
| 4H_V3_400x_cap2 | 989.19% | 454.44% | 18/200 |

December 4H passes (32/200 and 18/200). December **1H fails badly**: 188/200 and 189/200 random runs beat the model - the coin flip is decisively better. Actual 1H V3 +1,485% vs random median **+4,897%**.

Across all 28 controls run so far (7 months x 4 tests), only Dec 4H, Jan 4H and May 4H pass. Three in 28 is about what chance produces.

---

## 7. Goals vs. reality

| Goal | Target | Measured | Met? |
|---|---|---|---|
| Monthly ROI | > 700% | December: +89.11% / +68.11% / -96.66%. Only Jan Daily (+733.97%) has ever cleared 700%, once in 21 cells. | **No** |
| Max drawdown | < 5% | December V1: -23.04% (Daily), -55.79% (4H), -97.44% (1H). | **No** |
| Live risk | < 7% | 20% of equity at 500x = 100x notional; a 1% adverse move is the account. | **No** |

---

## 8. Bottom line

Seven consecutive months of 100% real Investing.com data, three timeframes, 21 independent tests, **1,654 pooled 1H trades** and 462 pooled 4H trades:

- December is **mildly positive on Daily and 4H**, but on 5 and 50 trades respectively, with -23% and -56% drawdowns, and **nothing is statistically significant**.
- December 1H loses **96.66%** and is beaten by a coin flip 188 times out of 200.
- **Observed significant results (1) are now fewer than noise would produce (1.05).**
- Pooled over seven months: 4H t = +0.84, 1H t = -0.77, **both V1 curves at -100.00%**.
- The stated goals are **not achievable** with this model under honest live timing.

Adding December did not strengthen the case. It added two more small positive cells with unacceptable drawdowns, one more badly negative 1H month, and pushed the count of significant findings below chance.

**Note on Jan 4H/1H:** loading all seven months as one continuous panel lets Dec 31 legitimately signal January's first entry - what a live trader sees. This adds one real trade to Jan 4H (t +1.63 -> +1.69) and Jan 1H (t -0.12 -> -0.04). Every other previously published cell is bit-for-bit identical.

---

*Raw results: `backtest_results/live_model/dec2025_to_june2026_live_all_tf.json`. Engine: `scripts/agba_metta_live.py`, `scripts/intraday_engine.py`. Raw price windows: `data/raw/intraday/*2025dec*`.*
