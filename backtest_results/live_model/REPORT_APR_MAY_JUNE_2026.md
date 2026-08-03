# April + May + June 2026 — Agba Metta, LIVE-CORRECT timing, Daily / 4H / 1H, V1 and V3

Data: 100% Investing.com (tvc4 history endpoint). No synthetic bars, no interpolation,
no envelope reconstruction. **Every April window saved with `envelope_fixes = 0`.**

## Coverage

| Month | Daily | 1H (3-asset aligned) | 4H |
|---|---:|---:|---:|
| **April 2026** | 22 sessions | **483 bars, 25 days** | **130 buckets** |
| May 2026 | 21 sessions | 479 bars, 25 days | 130 buckets |
| June 2026 | 22 sessions | 488 bars, 26 days | 132 buckets |

April raw windows added: `XAUUSD_2026apr_w1..w4`, `EURUSD_2026apr_w1a..w9a`,
`AUDUSD_2026apr_w1a..w9a`.

**One April note, verified not assumed:** 2026-04-03 was **Good Friday**. Gold returned
0 bars; EURUSD and AUDUSD each returned 21. That is a genuine exchange closure, not a
fetch gap — so 3-asset alignment is only possible on 25 of April's days. I checked each
symbol separately rather than assuming.

## Model timing (unchanged)

Signal candle closes → all 3 close UP = LONG, all 3 close DOWN = SHORT, mixed = skip →
**enter on the NEXT candle open** → 1% stop from the ACTUAL entry price → exit at that
candle's close unless stopped. 20% of equity split /3.

V1 = 500x, no cap.  V3 = 400x with a −2% per-bar basket loss cap.

## APRIL 2026

| TF | Config | Trades | WR | ROI | Max DD | Stops |
|---|---|---:|---:|---:|---:|---:|
| Daily | V1 500x | 14 | 42.9% | −91.56% | −95.88% | 7 |
| Daily | V3 400x cap | 14 | 42.9% | +561.49% | −9.61% | 7 |
| 4H | V1 500x | 83 | 51.8% | −95.79% | −97.47% | 9 |
| 4H | V3 400x cap | 83 | 51.8% | +42,744.04% | −5.88% | 9 |
| 1H | V1 500x | 270 | 44.4% | −99.86% | −99.94% | 3 |
| 1H | V3 400x cap | 270 | 44.4% | +145,473.63% | −19.53% | 3 |

## All three months side by side — raw edge, leverage stripped

| Month | TF | n | WR | mean/trade | t | p |
|---|---|---:|---:|---:|---:|---:|
| Apr | Daily | 14 | 42.9% | +0.0046% | +0.03 | 0.976 |
| Apr | 4H | 83 | 51.8% | +0.0120% | +0.33 | 0.741 |
| Apr | 1H | 270 | 44.4% | −0.0107% | −1.12 | 0.263 |
| May | Daily | 17 | 29.4% | −0.1708% | −1.30 | 0.194 |
| May | 4H | 67 | 53.7% | +0.0649% | **+2.13** | **0.033** |
| May | 1H | 246 | 48.8% | −0.0014% | −0.17 | 0.865 |
| Jun | Daily | 12 | 16.7% | −0.2608% | −1.79 | 0.074 |
| Jun | 4H | 64 | 54.7% | −0.0384% | −1.02 | 0.308 |
| Jun | 1H | 260 | 52.3% | +0.0049% | +0.50 | 0.617 |

## The May 4H result is now conclusively dead

Adding April gives the decisive out-of-sample test on the one cell that ever looked good:

- **9 tests run** (3 months × 3 timeframes). Bonferroni α = 0.05/9 = **0.00556**.
- May 4H p = 0.0332 → **fails**.
- Expected number of p<0.05 under pure noise across 9 tests: **0.45**. Observed: **1**.
  Exactly what noise produces.
- **4H t-stat by month: Apr +0.33 → May +2.13 → Jun −1.02.** It does not persist on
  either side.
- **Pooled 4H (Apr+May+Jun): n = 215, mean +0.0143%, t = +0.70, V1 = −100.00%.**
- **Pooled 1H (Apr+May+Jun): n = 777, mean −0.0025%, t = −0.47, V1 = −100.00%.**

777 pooled 1H trades is a large sample. t = −0.47 is not a small edge; it is no edge.

## Random-direction control (April)

Keep the exact bars where alignment fires, replace the signalled side with a coin flip,
200 runs, seed 7.

| TF | Config | Actual | Random median | Random runs ≥ actual |
|---|---|---:|---:|---:|
| 1H | V1 | −99.86% | −97.25% | 174 / 200 |
| 1H | V3 | +145,474% | +571,357% | 181 / 200 |
| 4H | V1 | −95.79% | −98.41% | 72 / 200 |
| 4H | V3 | +42,744% | +30,393% | 75 / 200 |

On April 1H, coin flips beat the real signal **87% of the time** — the alignment rule is
worse than random there. April 4H sits mid-distribution. Compare May 4H's 1/200: that
single strong cell is the same one that fails Bonferroni and reverses in both neighbours.

## V3's numbers are the cap, not edge

April 1H V3 prints +145,474% while the random median on the same bars is **+571,357%** —
random directions did *four times better*. The −2% cap truncates losses while gains
compound at 400x; any coin-flip sequence prints a large number. V1 (same signal, no cap)
loses 91–100% every month at every timeframe except May 4H.

## Against the stated goals

| Goal | Result across Apr–Jun |
|---|---|
| Monthly ROI > 700% | Only V3 (a cap artifact) and May-4H-V1; both reproduced by random directions |
| Max DD < 5% | Never met in 18 month×TF×config cells. Best is April 4H V3 at −5.88% |
| Live risk < 7% | A 1% stop at 400–500x is ~400–500% of allocated margin per leg |

## Bottom line

Three full months, three timeframes, **1,450 aligned 1H bars, 392 4H buckets, 65 daily
sessions, 9 independent tests**. The model shows no measurable edge under honest
next-candle timing. Daily is consistently worst (t = +0.03, −1.30, −1.79). The single
positive cell — May 4H — fails multiple-testing correction, reverses sign in both April
and June, and vanishes on pooling (t = +0.70, V1 −100%).

Adding April did not weaken an edge. It confirmed there was never one to weaken.
