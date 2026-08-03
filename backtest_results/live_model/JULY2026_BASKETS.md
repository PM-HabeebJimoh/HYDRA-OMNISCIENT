# July 2026 full backtest — Agba Metta with 4 substituted baskets

Core basket XAU/EUR/AUD removed and replaced by each candidate. Model rules
otherwise unchanged: regime from real yield -> alignment on the closed signal bar
-> enter next session open, exit that session's close, 20% equity split equally
across the 3 assets.

**Window:** 20 usable July sessions, 2026-07-01 to 2026-07-28. `2026-07-29` dropped
(GBPUSD, NZDUSD, USDCAD, USDJPY missing). Real yield stayed above 0.7 all month, so
regime = CONTRACTION = SHORT base direction; FADE baskets therefore traded LONG.

**Data limitation:** the xpairs files carry open/close only, no high/low, so the
model's **1% intraday stop could not be applied**. All runs are open->close. Costs
included per instrument.

---

## 1. AUDUSD + GBPUSD + USDCAD (FADE) — 4 trades

| signal | trade | side | AUDUSD | GBPUSD | USDCAD |
|---|---|---|---:|---:|---:|
| 07-07 | 07-08 | LONG | +0.014% | +0.240% | -0.176% |
| 07-13 | 07-14 | LONG | +0.824% | +0.315% | -0.678% |
| 07-17 | 07-20 | LONG | +0.387% | -0.149% | +0.392% |
| 07-23 | 07-24 | LONG | +0.187% | +0.105% | +0.071% |

| leverage | WR | return | maxDD | final equity |
|---:|---:|---:|---:|---:|
| 500 | 100% | **+58.57%** | 0.00% | $158,569 |
| 100 | 100% | +10.27% | 0.00% | $110,273 |
| 25 | 100% | +2.50% | 0.00% | $102,505 |

## 2. EURUSD + AUDUSD + USDCAD (FADE) — 4 trades

| leverage | WR | return | maxDD | final equity |
|---:|---:|---:|---:|---:|
| 500 | 75% | **+39.48%** | -4.54% | $139,476 |
| 100 | 75% | +7.39% | -0.91% | $107,391 |
| 25 | 75% | +1.82% | -0.23% | $101,824 |

## 3. GBPUSD + NZDUSD + USDCAD (FADE) — 3 trades

| leverage | WR | return | maxDD | final equity |
|---:|---:|---:|---:|---:|
| 500 | 100% | **+59.22%** | 0.00% | $159,220 |
| 100 | 100% | +10.42% | 0.00% | $110,419 |
| 25 | 100% | +2.54% | 0.00% | $102,541 |

## 4. NZDUSD + USDCAD + USDJPY (FOLLOW) — 1 trade

Only one alignment all month: signal 07-22 -> trade 07-23, SHORT.

| leverage | WR | return | maxDD | final equity |
|---:|---:|---:|---:|---:|
| 500 | 100% | **+13.66%** | 0.00% | $113,658 |
| 25 | 100% | +0.68% | 0.00% | $100,683 |

---

## Summary

| basket | dir | trades | WR | ret @25x | ret @500x | DD @25x |
|---|---|---:|---:|---:|---:|---:|
| AUDUSD+GBPUSD+USDCAD | FADE | 4 | 100% | +2.50% | +58.57% | 0.00% |
| EURUSD+AUDUSD+USDCAD | FADE | 4 | 75% | +1.82% | +39.48% | -0.23% |
| GBPUSD+NZDUSD+USDCAD | FADE | 3 | 100% | +2.54% | +59.22% | 0.00% |
| NZDUSD+USDCAD+USDJPY | FOLLOW | 1 | 100% | +0.68% | +13.66% | 0.00% |

**Benchmark — the core basket in the same month:**

| XAUUSD+EURUSD+AUDUSD | trades | WR | return | DD |
|---|---:|---:|---:|---:|
| ORIGINAL @25x | 5 | 40% | **-2.75%** | -5.89% |
| REVERSED @25x | 5 | 60% | +2.36% | -2.24% |
| ORIGINAL @500x | 5 | — | **-76.98%** | ends $23,017 |

All four substitutes beat the core basket in July 2026.

---

## Three cautions before reading anything into this

**1. July was inside the selection window.** These 4 baskets were chosen by
searching 196 combinations over Jan–Jul 2026. July is part of the data that picked
them, so these results are **in-sample** — not an independent test.

**2. The trade counts are 4, 4, 3 and 1.** No statistic is meaningful at that size.
Three baskets show "100% win rate" and "0.00% drawdown" simply because they had no
losing day in a 20-session month.

**3. "199.75x at DD<5%" is an artifact, not a risk finding.** Drawdown stayed 0% at
every leverage only because no trade lost. Actual single-day exposure at 20% equity
split 3 ways, if each leg moves 1% against you:

| leverage | one-day loss | |
|---:|---:|---|
| 500x | -100% | account wiped |
| 200x | -40% | severe |
| 100x | -20% | severe |
| 50x | -10% | survivable |
| 25x | -5% | survivable |

July simply never produced that day. It will occur.

**Verdict:** all four substitute baskets outperformed XAU/EUR/AUD in July 2026, and
the core basket lost money in both its original direction (-2.75% at 25x, -76.98%
at 500x). But with 1–4 in-sample trades each, July alone cannot confirm the
ranking. Out-of-sample 2025 data for these pairs — with high/low so the 1% stop
applies — remains the test that would settle it.

Reproduce: `research.july2026_baskets`, `research.july2026_context`
