# What the 3-Alignment Actually Is — Cross-Pair Study

**Question:** when XAUUSD + EURUSD + AUDUSD all move the same way, what happens to every other
major currency pair?

**Sample:** 129 daily sessions (2025-01-02 → 2026-04-01) where all six additional majors have
real daily open/close, intersected with the existing core panel. **58 of those 129 days are
Agba Metta signal days** (27 all-down, 31 all-up).

**Data:** Investing.com spot daily bars — GBPUSD (pair 2), USDJPY (3), USDCHF (4), USDCAD (7),
NZDUSD (8). All real, no synthetic fills.

Sign convention: for USD-quoted pairs (GBPUSD, NZDUSD) a *fall* = USD stronger. For USD-base
pairs (USDJPY, USDCHF, USDCAD) a *rise* = USD stronger.

---

## FINDING 1 — The 3-alignment is a US-dollar signal, not a gold/EUR/AUD signal

On all-3-DOWN days, every other major moves the same way — the dollar is up across the board:

| Pair | mean move | USD stronger on |
|---|---:|---:|
| GBPUSD | −0.384 % | **92.6 %** of days |
| NZDUSD | −0.557 % | **92.6 %** of days |
| USDCHF | +0.308 % | 81.5 % |
| USDCAD | +0.251 % | 77.8 % |
| USDJPY | +0.132 % | 66.7 % |

On all-3-UP days it mirrors exactly — the dollar is down:

| Pair | mean move | USD stronger on |
|---|---:|---:|
| GBPUSD | +0.527 % | **0.0 %** of days |
| NZDUSD | +0.633 % | 3.2 % |
| USDCHF | −0.572 % | 12.9 % |
| USDCAD | −0.405 % | 9.7 % |
| USDJPY | −0.265 % | 48.4 % |

On non-aligned days every number collapses toward the 50–60 % coin-flip baseline.

**GBPUSD rose on 100 % of all-3-UP days (31/31) and fell on 92.6 % of all-3-DOWN days.**
Correlation with the core basket on signal days: NZDUSD **+0.82**, GBPUSD **+0.78**,
USDCHF **+0.75**, USDCAD **+0.66**, USDJPY **+0.47**.

On 94.8 % of signal days at least 3 of the 5 other majors confirm the same dollar direction;
on 48.3 % *all five* confirm.

**Conclusion: "gold down + EUR down + AUD down" is a proxy for "USD up".** The model is not
finding anything specific to gold, the euro or the Aussie — it is detecting a broad dollar day.
The three chosen assets are simply three of the most dollar-sensitive instruments available.

---

## FINDING 2 — The other pairs would NOT have produced a 100 % win rate

This is the most important result in the whole study. Same days, same direction, same open→close:

| Instrument | n | Day win rate | mean return |
|---|---:|---:|---:|
| **gold** | 58 | **100.0 %** | +1.5675 % |
| **eur** | 58 | **100.0 %** | +0.4804 % |
| **aud** | 58 | **100.0 %** | +0.6175 % |
| GBPUSD | 58 | 96.6 % | +0.4607 % |
| NZDUSD | 58 | 93.1 % | +0.5976 % |
| USDCHF | 58 | 84.5 % | +0.4488 % |
| USDCAD | 58 | 84.5 % | +0.3331 % |
| USDJPY | 58 | **58.6 %** | +0.2030 % |

The three core assets score **exactly 100.0 %**. Every other pair — responding to the *same*
dollar move on the *same* days — lands between 58.6 % and 96.6 %.

That gap is the look-ahead, isolated and measured. gold/EUR/AUD are 100 % **because the signal is
defined as their own close vs open** — `close < open` is the same statement as "the short was
profitable". The other five pairs were never part of the signal definition, so they show what the
dollar move *actually* delivers: 58–97 %, not 100 %.

**USDJPY at 58.6 % is the cleanest evidence.** It is a genuine major, strongly dollar-driven, and
it wins barely more than a coin flip on exactly the days the model calls perfect.

---

## FINDING 3 — Adding pairs makes the model worse, not better

Equal-weight basket, model direction, no stop:

| Universe | Day WR | mean/day | worst day |
|---|---:|---:|---:|
| **gold alone** | 100.0 % | **+1.5675 %** | +0.028 % |
| **core 3 (current)** | 100.0 % | +0.8885 % | +0.148 % |
| core 3 + GBP + NZD | 100.0 % | +0.7447 % | +0.081 % |
| FX-only (eur, aud, GBP, NZD) | 100.0 % | +0.5391 % | +0.025 % |
| core 3 + all 5 | **98.3 %** | +0.5886 % | **−0.176 %** |

Adding pairs **dilutes** return and eventually **breaks the 100 % win rate**. The full 8-asset
basket produces the first losing day in the sample. Diversification cannot help here, because
every added pair is the same dollar bet with a smaller amplitude — more correlation, less edge.

Note gold alone beats the 3-asset basket (+1.57 % vs +0.89 %). The basket exists to damp variance,
not to raise return.

---

## FINDING 4 — Why gold carries the model, and why the 1 % stop is mis-sized

Average absolute daily move across the sample:

| Instrument | avg \|move\| | 1 % stop = |
|---|---:|---:|
| **gold** | **1.209 %** | 0.83× a typical day |
| AUD / NZDUSD | 0.466 % | 2.15× |
| USDJPY | 0.416 % | 2.40× |
| USDCHF | 0.386 % | 2.59× |
| EUR | 0.380 % | 2.63× |
| GBPUSD | 0.375 % | 2.67× |
| USDCAD | 0.281 % | 3.56× |

Gold moves **3.2× more than the average FX major**. The 1 % hard stop sits *below* gold's typical
daily range but at 2–3.5× the typical range of every currency pair.

Consequence: the stop is effectively **gold-only**. On signal days gold's open→close exceeds 1 % on
44.8 % of days, versus 3.4 % (USDCAD) to 20.7 % (AUD) for the currencies. This confirms the earlier
per-pair loss analysis — all 12 stop-outs in the 2025+2026 sample were XAUUSD, EURUSD had literally
zero. **Gold supplies most of the return and essentially all of the risk.**

---

## FINDING 5 — The causal test: the alignment predicts nothing, on any pair

Signal read from the **prior** session, trade the next day:

| Pair | n | Win rate | mean/trade | t-stat |
|---|---:|---:|---:|---:|
| GBPUSD | 57 | 47.4 % | −0.0400 % | −0.58 |
| NZDUSD | 57 | 52.6 % | −0.0054 % | −0.06 |
| USDJPY | 57 | 59.6 % | +0.1032 % | +1.27 |
| USDCHF | 57 | 50.9 % | +0.0576 % | +0.71 |
| USDCAD | 57 | 57.9 % | +0.0747 % | +1.57 |
| gold | 57 | 50.9 % | +0.1008 % | +0.45 |
| eur | 57 | 52.6 % | +0.0016 % | +0.02 |
| aud | 57 | 49.1 % | +0.0148 % | +0.18 |

**Not one instrument reaches statistical significance** (all |t| < 2). Win rates sit at 47–60 %,
i.e. noise. The 100 % same-day win rate collapses to a coin flip the moment the signal is read
before the bar it trades.

This is the same conclusion reached on the core 3, now reproduced independently on five pairs that
were never involved in constructing the signal. It rules out the possibility that the effect was
an artifact of the specific three assets chosen.

---

## Summary

1. The 3-alignment is a **broad US-dollar signal**. Every major confirms it (corr +0.47 to +0.82);
   GBPUSD moved with it on 100 % of all-3-UP days.
2. The dollar move on those days is **real**. What is not real is the 100 % win rate — the other
   five pairs, hit by the identical move, score **58.6 %–96.6 %**.
3. That 100 % vs 58–97 % gap **is** the look-ahead, now measured on out-of-universe instruments.
4. **Adding pairs degrades the model** — more dilution, more correlation, and the first losing day.
5. **Gold is the engine and the risk**: 3.2× the volatility of the FX majors, and the only asset
   the 1 % stop can realistically reach.
6. Lagged one session, **nothing predicts anything** — every pair, |t| < 2.

The most useful practical takeaway: if you want to keep trading this structure, the universe
choice is not where the edge is. Gold alone outperforms the basket on these days, and the stop is
sized for gold, so the two FX legs are contributing dilution and very little protection.
