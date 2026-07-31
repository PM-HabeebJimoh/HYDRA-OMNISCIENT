# May + June 2026 — Agba Metta, LIVE-CORRECT timing, Daily / 4H / 1H, V1 and V3

Data: 100% Investing.com (tvc4 history endpoint). No synthetic bars, no interpolation,
no envelope reconstruction. Every window validated on save.

## Coverage

| Month | Daily | 1H (3-asset aligned) | 4H |
|---|---:|---:|---:|
| May 2026 | 21 sessions | **479 bars, 25 days** | **130 buckets** |
| June 2026 | 22 sessions | 488 bars, 26 days | 132 buckets |

May raw windows added: `XAUUSD_2026may_w1..w4`, `EURUSD_2026may_w1a..w9a`,
`AUDUSD_2026may_w1a..w9a`.

Envelope validation: `envelope_fixes = 0` on every window except
`EURUSD_2026may_w2a` at 1/73 bars (1.4%), a 4-decimal rounding boundary — far under
the 10% misalignment threshold. Re-verified: 0 remaining violations.

4H is resampled from 1H into 00/04/08/12/16/20 UTC buckets — the provider silently
ignores `resolution=240` and returns hourly stamps.

## Model timing (unchanged)

Signal candle closes → all 3 close UP = LONG, all 3 close DOWN = SHORT, mixed = skip
→ **enter on the NEXT candle open** → 1% stop from the ACTUAL entry price → exit at
that candle's close unless stopped. 20% of equity split /3.

V1 = 500x, no cap.  V3 = 400x with a −2% per-bar basket loss cap.

## MAY 2026

| TF | Config | Trades | S/L | WR | ROI | Max DD | Stops |
|---|---|---:|---|---:|---:|---:|---:|
| Daily | V1 500x | 17 | — | 29.4% | −99.82% | −99.87% | 11 |
| Daily | V3 400x cap | 17 | — | 29.4% | +351.61% | −11.42% | 11 |
| 4H | V1 500x | 67 | — | 53.7% | **+865.99%** | −75.67% | 1 |
| 4H | V3 400x cap | 67 | — | 53.7% | **+26,386.83%** | −8.73% | 1 |
| 1H | V1 500x | 246 | — | 48.8% | −92.68% | −99.28% | 2 |
| 1H | V3 400x cap | 246 | — | 48.8% | +44,175.98% | −15.01% | 2 |

## JUNE 2026

| TF | Config | Trades | S/L | WR | ROI | Max DD | Stops |
|---|---|---:|---|---:|---:|---:|---:|
| Daily | V1 500x | 12 | 7/5 | 16.7% | −99.87% | −99.87% | 10 |
| Daily | V3 400x cap | 12 | 7/5 | 16.7% | +75.37% | −13.19% | 10 |
| 4H | V1 500x | 64 | 39/25 | 54.7% | −99.99% | −100.00% | 11 |
| 4H | V3 400x cap | 64 | 39/25 | 54.7% | +3,001.34% | −7.75% | 11 |
| 1H | V1 500x | 260 | 145/115 | 52.3% | −91.72% | −98.46% | 6 |
| 1H | V3 400x cap | 260 | 145/115 | 52.3% | +589,802.48% | −17.37% | 6 |

## Raw edge, leverage stripped (per-trade basket return at 1x)

| Month | TF | n | WR | mean/trade | t |
|---|---|---:|---:|---:|---:|
| May | Daily | 17 | 29.4% | −0.1708% | −1.30 |
| May | 4H | 67 | 53.7% | **+0.0649%** | **+2.13** |
| May | 1H | 246 | 48.8% | −0.0014% | −0.17 |
| June | Daily | 12 | 16.7% | −0.2608% | −1.79 |
| June | 4H | 64 | 54.7% | −0.0384% | −1.02 |
| June | 1H | 260 | 52.3% | +0.0049% | +0.51 |

## The May 4H result — and why it is not an edge

May 4H is the only positive t-stat in the whole study (+2.13, two-sided p = 0.033),
and its V1 return is genuinely positive (+866%). It deserves a direct answer, so I
tested it three ways:

**1. Multiple testing.** Six independent tests were run (2 months × 3 timeframes).
Bonferroni threshold is 0.05/6 = 0.0083. p = 0.033 **does not survive**. Finding one
result at p<0.05 out of six is the expected outcome of pure noise.

**2. Out-of-sample.** The very next month reverses the sign: June 4H t = **−1.02**.

**3. Pooling.** May + June 4H combined: n = 132, mean +0.0157%/trade, **t = +0.65**.
The pooled V1 result is **−99.94%** — the May gain is entirely erased.

So the honest reading is: May 4H is a favourable draw, not a repeatable effect.

## Random-direction control

Keep the exact bars where alignment fires, replace the signalled side with a coin
flip, 200 runs, seed 7.

| Month | TF | Config | Actual | Random median | Random runs ≥ actual |
|---|---|---|---:|---:|---:|
| May | 1H | V1 | −92.68% | −89.73% | 109 / 200 |
| May | 1H | V3 | +44,176% | +54,187% | 117 / 200 |
| May | 4H | V1 | +866% | −90.16% | **1 / 200** |
| May | 4H | V3 | +26,387% | +6,013% | **4 / 200** |
| June | 1H | V1 | −91.72% | −97.25% | 72 / 200 |
| June | 1H | V3 | +589,802% | +370,256% | 73 / 200 |
| June | 4H | V1 | −99.99% | −98.09% | 185 / 200 |
| June | 4H | V3 | +3,001% | +9,461% | 172 / 200 |

May 4H is the one cell where the control looks strong (1/200). But this is the same
single result already shown to fail Bonferroni and to reverse out-of-sample — the
control confirms May 4H's directions happened to be right that month, not that the
rule predicts direction. Every other cell sits mid-distribution: coin flips match or
beat the real signal 36%–93% of the time.

## What V3's huge numbers actually are

V3's +589,802% (June 1H) and +44,176% (May 1H) are not edge. The −2% cap truncates the
left tail while gains compound unbounded at 400x. Random directions on the same bars
produce medians of the same order (+370,256% and +54,187% — the May random median is
*higher* than the actual). V1, the same signal without the cap, loses 92–93% in both
months.

## Against the stated goals

| Goal | Result |
|---|---|
| Monthly ROI > 700% | Only V3 and May-4H-V1 clear it; both reproduced by random directions |
| Max DD < 5% | Never met. Best is May 4H V3 at −8.73%; V1 configs run −75% to −100% |
| Live risk < 7% | A 1% stop at 400–500x is ~400–500% of allocated margin per leg |

## Bottom line

Across two full months and three timeframes — 6 independent tests, 958 aligned 1H
bars, 262 4H buckets, 43 daily sessions — the model shows no measurable edge under
honest next-candle timing. Daily is consistently the worst (t = −1.30 and −1.79). The
single positive cell (May 4H) fails multiple-testing correction, flips sign the next
month, and vanishes on pooling.
