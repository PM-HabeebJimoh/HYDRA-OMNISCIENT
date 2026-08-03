# Agba Metta Model - Live-Correct Backtest, January -> June 2026

**Data:** 100% real Investing.com (tvc4 history endpoint). No synthetic bars, no interpolation, no approximations, no filled gaps. Every January window saved with `envelope_fixes = 0`.

**Timing (live-correct):** signal candle closes -> all 3 of XAUUSD/EURUSD/AUDUSD close UP = LONG, all 3 close DOWN = SHORT, mixed = skip -> **enter on the NEXT candle open** -> 1% stop from the *actual* entry price -> exit at that candle's close unless stopped intrabar.

**Sizing:** 20% of equity split across 3 assets. **V1** = 500x, no cap. **V3** = 400x with a -2% per-bar basket loss cap.

## Data verification

The repo already held a partial January slice (Jan 1-14). I re-fetched the whole month independently and compared:

- **507 overlapping bars, ZERO mismatches** against the previously stored data.
- Engine reproduces the previously published February and March figures exactly.
- Superseded partial files (`*2026w0*.json`) were removed - fully contained in the new January windows, so keeping both would double-count.

---

## 1. Coverage

| Month | 1H bars | 4H buckets | Daily sessions |
|---|---:|---:|---:|
| January 2026 | 480 | 131 | 22 |
| February 2026 | 458 | 124 | 20 |
| March 2026 | 508 | 137 | 22 |
| April 2026 | 483 | 130 | 22 |
| May 2026 | 479 | 130 | 21 |
| June 2026 | 488 | 132 | 22 |

January: XAUUSD 480 / EURUSD 504 / AUDUSD 504 bars; **480 aligned** across 26 days, all 21 trading days present.

---

## 2. January 2026 - the first genuinely positive month

| TF | Trades | Win rate | V1 (500x) | V1 max DD | V3 (400x, -2% cap) | V3 max DD |
|---|---:|---:|---:|---:|---:|---:|
| Daily | 10 | 60.0% | 733.97% | -82.32% | 2,350.52% | -7.76% |
| 4H | 56 | 60.7% | 353.22% | -83.10% | 24,699.73% | -5.88% |
| 1H | 200 | 47.5% | -98.22% | -98.87% | 138,234.15% | -14.47% |

**This is the first month in six where V1 makes money on Daily and 4H.** Daily +733.97% (60.0% WR), 4H +353.22% (60.7% WR). I am not going to soften that - it is a real result on real data.

**But it does not survive scrutiny, for four reasons:**

**(a) It is not statistically significant.** Jan Daily t = +1.76 (p = 0.1120), Jan 4H t = +1.63 (p = 0.1085). Neither clears even the uncorrected 0.05 bar, let alone Bonferroni at 0.002778.

**(b) The drawdowns are catastrophic anyway.** V1 Daily draws down **-82.32%** and 4H **-83.10%** *while winning*. An account that loses 82% of its value en route to a gain is not tradeable, and it violates the <5% drawdown goal by a factor of 16.

**(c) January 1H is negative** (-98.22%, t = -0.12). The same signal on the same month at a finer timeframe destroys the account.

**(d) It does not repeat.** February through June are almost uniformly negative.

---

## 3. All six months

| Month | TF | n | WR | V1 (500x) | V1 max DD | V3 (400x cap) | V3 max DD |
|---|---|---:|---:|---:|---:|---:|---:|
| January 2026 | Daily | 10 | 60.0% | 733.97% | -82.32% | 2,350.52% | -7.76% |
| January 2026 | 4H | 56 | 60.7% | 353.22% | -83.10% | 24,699.73% | -5.88% |
| January 2026 | 1H | 200 | 47.5% | -98.22% | -98.87% | 138,234.15% | -14.47% |
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

V1 is destroyed in **15 of 18** month/timeframe cells. The three exceptions are Jan Daily, Jan 4H and May 4H - and all three carry drawdowns of -75% to -83%.

---

## 4. Raw edge and 18-test Bonferroni

| Month | TF | n | WR | Mean / trade | t | p (two-sided) |
|---|---|---:|---:|---:|---:|---:|
| January 2026 | Daily | 10 | 60.0% | +0.4619% | +1.76 | 0.1120 |
| January 2026 | 4H | 56 | 60.7% | +0.0952% | +1.63 | 0.1085 |
| January 2026 | 1H | 200 | 47.5% | -0.0016% | -0.12 | 0.9070 |
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

**Bonferroni over 18 tests:** alpha = 0.05/18 = **0.002778**.
Smallest p is **May 4H, p = 0.0371** - does **not** survive (13x too large).
Expected p<0.05 under pure noise = **0.9**. Observed = **1**.

**Exactly one hit in eighteen tests is what randomness delivers.** Twelve of the eighteen t-stats are negative.

---

## 5. Month-to-month: the edge never persists

4H t-stat by month:

| Jan | Feb | Mar | Apr | May | Jun |
|---:|---:|---:|---:|---:|---:|
| +1.63 | -0.67 | -0.47 | +0.26 | +2.13 | -0.94 |

Positive, negative, negative, positive, positive, negative. This is a coin flip, not an edge. A real edge is *persistent*; this one changes sign four times in six months.

**Pooled January -> June (the full six months):**

| Pooled TF | n | WR | Mean / trade | t | V1 (500x) | V1 max DD |
|---|---:|---:|---:|---:|---:|---:|
| 4H | 411 | 50.61% | +0.0111% | +0.63 | -100.00% | -100.00% |
| 1H | 1460 | 48.77% | -0.0023% | -0.49 | -100.00% | -100.00% |

January's strong months lift pooled 4H from -0.07 to **+0.63** - still nowhere near significance on n = 411 trades. Pooled 1H is **-0.49** on n = 1460. **Both pooled V1 curves still end at -100.00%:** the good months cannot outrun the bad ones at 500x.

---

## 6. Random-direction control - January

Keep the exact bars where 3-asset alignment fires, coin-flip the side, 200 runs, seed 7.

| Test | Actual | Random median | Random runs beating actual |
|---|---:|---:|---:|
| 1H_V1_500x | -98.22% | -94.27% | 129/200 |
| 1H_V3_400x_cap2 | 138,234.15% | 176,969.93% | 119/200 |
| 4H_V1_500x | 353.22% | -85.83% | 21/200 |
| 4H_V3_400x_cap2 | 24,699.73% | 5,985.84% | 22/200 |

**This is the one honest point in the model's favour.** January 4H beats the coin flip 179/200 (only 21 random runs did better) and V3 22/200. That is a genuine signal *in that month*.

But January 1H fails the same test (129/200 and 119/200 - the coin flip wins). And across all six months only January 4H and May 4H pass, out of 24 controls. Two passes in 24 is close to the ~1.2 you would expect from chance alone at this threshold.

---

## 7. V3 remains a cap artifact

| Cell | Model | Coin-flip median | Verdict |
|---|---:|---:|---|
| Jan 1H V3 | +138,234% | **+176,970%** | random better |
| Feb 1H V3 | +226,130% | **+489,942%** | random ~2x better |
| Apr 1H V3 | +145,474% | **+571,357%** | random ~4x better |
| Mar 4H V3 | +52,329% | **+118,680%** | random ~2x better |

Strip the cap and keep the identical signal (V1): -91% to -100% in 15 of 18 cells. The -2% basket cap assumes you always fill at exactly -2% on a 400x position through gaps and news. You will not.

---

## 8. Goals vs. reality

| Goal | Target | Measured | Met? |
|---|---|---|---|
| Monthly ROI | > 700% | Jan Daily +733.97% clears it - **once in 18 cells**. Pooled V1 -100.00%. | **No** |
| Max drawdown | < 5% | Even in the winning month: -82.32% (Daily), -83.10% (4H). | **No** |
| Live risk | < 7% | 20% of equity at 500x = 100x notional; a 1% adverse move is the account. | **No** |

January is the one month that hits the ROI target - and it does so with a **-82% drawdown**, which is 16x the risk limit. You cannot have the return without the drawdown; they are the same trades.

---

## 9. Bottom line

Six consecutive months of 100% real Investing.com data, three timeframes, 18 independent tests, **1,460 pooled 1H trades** and 411 pooled 4H trades:

- **January is real and positive** on Daily (+733.97%) and 4H (+353.22%), and January 4H genuinely beats its coin-flip control. This is the strongest evidence found in six months of testing.
- It is still **not statistically significant** (t = +1.76 and +1.63, p > 0.10), it comes with **-82% drawdowns**, and January 1H loses 98%.
- The edge **does not persist**: the 4H t-stat flips sign four times across the six months.
- Pooled over all six months: 4H t = +0.63, 1H t = -0.49, and **both V1 curves still end at -100.00%**.
- The stated goals - 700%/month, <5% DD, <7% risk - are **not simultaneously achievable** with this model.

The original +1,026% headline came from entering on the same candle whose close created the signal. That is look-ahead. With entry moved to the next candle open, as live trading requires, what remains is one good month, one lucky month, and four bad ones.

**Note on Feb 4H:** loading all six months as one continuous panel lets Jan 30 20:00 legitimately signal the first February entry - which is what a live trader sees. This adds one real trade to February 4H (t -0.56 -> -0.67). Every other previously published cell is bit-for-bit identical.

---

*Raw results: `backtest_results/live_model/jan_to_june_2026_live_all_tf.json`. Engine: `scripts/agba_metta_live.py`, `scripts/intraday_engine.py`. Raw price windows: `data/raw/intraday/*2026jan_*`.*
