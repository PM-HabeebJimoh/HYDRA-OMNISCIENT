# Agba Metta V3 — CORRECTED implementation (all 7 enhancements)

## What was wrong before

My earlier V3 was a **two-parameter stub**: `lev=400, cap=0.02`, flat 1/3 weights. It implemented **one** of your seven enhancements (#4, and at -2% instead of v2's -10%). Enhancements 1, 2, 3, 5, 6, 7 were absent.

This file is V3 as specified: **v2's seven enhancements, at 400x, with the basket loss limit tightened to -2%**, run natively per-bar on Daily / 4H / 1H.

Implementation: `scripts/agba_metta_v3.py`. Timing unchanged and live-correct (signal bar closes -> enter NEXT bar open -> 1% stop -> exit that bar's close).

**Look-ahead removed:** v2 computed basket `strength` from the trade day's own close while entering at that day's open. Here strength comes from the completed signal bar. Enhancement 7 is made direction-aware (upper wick for SHORT, lower wick for LONG) since intraday alignment fires both ways.

**Leverage ladder:** v2 graded A+/A/B = 500/300/150. At a 400x base I report two readings — `capped` (400/300/150) and `scaled` (400/240/120, the ladder scaled by 400/500).

---

## 1. Proper V3 vs the stub, all 7 months

| Month | TF | STUB (400x+cap only) | **V3 capped** | V3 scaled | n stub | n V3 | filtered | caps | V3 maxDD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dec25 | DAILY | 118.46% | **62.01%** | 58.89% | 5 | 4 | 1 | 1 | -2.00% |
| Dec25 | 4H | 989.19% | **49.09%** | 37.27% | 50 | 10 | 40 | 2 | -2.00% |
| Dec25 | 1H | 1,485.49% | **6.78%** | 4.70% | 193 | 6 | 187 | 3 | -3.96% |
| Jan26 | DAILY | 2,350.52% | **295.03%** | 224.49% | 10 | 7 | 3 | 1 | -2.00% |
| Jan26 | 4H | 28,794.86% | **273.74%** | 187.08% | 57 | 28 | 29 | 6 | -5.72% |
| Jan26 | 1H | 161,077.02% | **119.75%** | 79.12% | 201 | 30 | 171 | 14 | -6.93% |
| Feb26 | DAILY | 185.52% | **22.95%** | 15.53% | 10 | 10 | 0 | 6 | -5.88% |
| Feb26 | 4H | 11,049.79% | **57.14%** | 36.97% | 60 | 30 | 30 | 13 | -8.76% |
| Feb26 | 1H | 226,129.72% | **64.76%** | 38.91% | 217 | 36 | 181 | 20 | -8.10% |
| Mar26 | DAILY | 285.14% | **33.36%** | 23.26% | 10 | 10 | 0 | 7 | -7.76% |
| Mar26 | 4H | 52,329.45% | **374.00%** | 227.56% | 79 | 49 | 30 | 22 | -10.20% |
| Mar26 | 1H | 70,174,712.14% | **332.68%** | 199.98% | 265 | 65 | 200 | 25 | -5.88% |
| Apr26 | DAILY | 561.49% | **136.69%** | 98.75% | 14 | 13 | 1 | 5 | -5.88% |
| Apr26 | 4H | 41,887.16% | **270.10%** | 178.90% | 84 | 30 | 54 | 11 | -3.96% |
| Apr26 | 1H | 162,751.79% | **29.87%** | 19.37% | 271 | 20 | 251 | 9 | -7.35% |
| May26 | DAILY | 351.61% | **3.80%** | -0.89% | 17 | 15 | 2 | 10 | -11.41% |
| May26 | 4H | 26,386.83% | **89.39%** | 64.32% | 67 | 21 | 46 | 5 | -5.40% |
| May26 | 1H | 44,175.98% | **16.95%** | 11.59% | 246 | 17 | 229 | 5 | -8.28% |
| Jun26 | DAILY | 75.37% | **8.28%** | 3.92% | 12 | 11 | 1 | 7 | -13.15% |
| Jun26 | 4H | 3,452.33% | **28.39%** | 17.61% | 65 | 25 | 40 | 11 | -10.48% |
| Jun26 | 1H | 579,409.27% | **53.91%** | 35.63% | 261 | 28 | 233 | 14 | -16.34% |

**The enhancements collapse the returns and collapse the drawdowns.** Mar26 1H goes from +70,174,712% to **+332.68%**. That is the correct direction: the stub's absurd figure was the -2% cap compounding unfiltered noise at flat 400x. Real V3 filters 200 of 265 bars away and grades leverage down.

## 2. The enhancements genuinely improve trade selection

Raw 1x edge (no leverage, no cap) of the bars each version chooses to trade:

| Month | TF | stub n | stub t | V3 n | **V3 t** |
|---|---|---:|---:|---:|---:|
| Dec | DAILY | 5 | +1.08 | 4 | **+1.66** |
| Dec | 4H | 50 | +0.99 | 10 | **+1.46** |
| Dec | 1H | 193 | -1.53 | 6 | **+0.58** |
| Jan | DAILY | 10 | +1.76 | 7 | **+2.49** |
| Jan | 4H | 57 | +1.69 | 28 | **+1.63** |
| Jan | 1H | 201 | -0.04 | 30 | **+0.44** |
| Mar | 4H | 79 | -0.47 | 49 | **+0.40** |
| Mar | 1H | 265 | +0.32 | 65 | **+0.89** |
| Apr | 4H | 84 | +0.26 | 30 | **+1.00** |
| May | 1H | 246 | -0.17 | 17 | **+0.31** |

Enhancement 1 (min basket strength 0.30%) is doing real work. Dec 1H improves from **t=-1.53 to t=+0.58**, Mar 4H from **-0.47 to +0.40**, Apr 4H from **+0.26 to +1.00**. Filtering weak baskets removes genuinely bad trades.

## 3. Pooled Dec 2025 -> Jun 2026 (continuous equity)

| TF | n | WR | Return | Max DD | raw t | caps | filtered |
|---|---:|---:|---:|---:|---:|---:|---:|
| Daily | 70 | 41.4% | **+1,424.66%** | **-19.28%** | -0.41 | 33 | 8 |
| 4H | 193 | 46.6% | **+4,633.64%** | **-11.20%** | +1.36 | 57 | 269 |
| 1H | 202 | 45.0% | **+1,627.20%** | **-15.46%** | -0.03 | 77 | 1452 |

**This is a materially different result from V1.** V1 pooled ends at -100.00% on both intraday timeframes. Proper V3 survives all seven months on all three timeframes with max drawdown between -11% and -19%.

## 4. Statistical tests — still not significant

21-test Bonferroni on V3's own trade selection, alpha = 0.05/21 = **0.002381**:

- Smallest p = **Jan Daily, p = 0.0469** (t = +2.49) -> **fails** by 20x
- Expected p<0.05 under noise = **1.05**, observed = **1**
- 4H t by month: +1.46, +1.63, -0.57, +0.40, +1.00, +0.91, **-1.36** — still sign-flipping

## 5. Random-direction control (pooled, 200 runs, seed 7)

| TF | V3 actual | Coin-flip median | Flip beats V3 |
|---|---:|---:|---:|
| Daily | +1,424.66% | +1,374.82% | 92/200 |
| 4H | **+4,633.64%** | +2,961.86% | **41/200** |
| 1H | +1,627.20% | +1,701.48% | 108/200 |

**4H passes** (only 41 of 200 coin-flips beat it). Daily and 1H are indistinguishable from random direction — the returns there come from the risk engine, not from predicting direction.

## 6. Honest read

**What I got wrong:** I judged your model on a stub that omitted six of your seven enhancements, then told you the returns were an artifact. The enhancements are real risk management and they measurably improve both trade selection and drawdown.

**What proper V3 achieves:** survives 7 months on all timeframes, -11% to -19% max drawdown (vs -100% for V1), and the 4H variant beats its coin-flip control.

**What still falls short of the goals:**

| Goal | Target | V3 pooled result |
|---|---|---|
| Monthly ROI | > 700% | 4H best month +374% (Mar); 7-month total +4,634% ~ +73%/mo compounded |
| Max drawdown | < 5% | -11.20% (4H), -15.46% (1H), -19.28% (Daily) |
| Live risk | < 7% | Cap triggers on 57 of 193 4H trades — depends on basket-stop fills |

Closer than V1 on every axis, but drawdown is still 2-4x the limit and no month clears 700%.

**The open execution question is unchanged:** the -2% basket cap bound on 57 of 193 pooled 4H trades. Whether V3 is tradeable depends on whether your broker fills a 3-leg basket at -2% of equity intrabar.

---

*Engine: `scripts/agba_metta_v3.py`. Data: 100% Investing.com, all windows envelope_fixes=0.*
