# POSITIONING — THE LAST PRE-CHART CATEGORY

You said go for direction. I went after the one pre-chart dataset that is
*supposed* to carry sign: **who is already positioned, and how crowded.**

**Data obtained (real, official, free):** CFTC Commitments of Traders,
legacy futures-only, via the CFTC Public Reporting Environment Socrata API.

- `data/raw/cot/cot_3assets.json` — 48 weeks × GOLD/COMEX, EURO FX/CME,
  AUSTRALIAN DOLLAR/CME (Sep 2025–Jul 2026)
- `data/raw/oos/cot_gold_hist.csv` — **352 weeks** of gold COT (Dec 2018–Aug 2025)
- `data/raw/oos/gold_weekly.json` — 348 weekly Investing.com gold closes

This is genuinely pre-chart: it is *who is loaded up*, not what price did.

## The timing trap, handled first

COT positions are **as of Tuesday close** but **published Friday 15:30 ET**.
Using the Tuesday date is a 3-day look-ahead and is how most COT "edges" are
manufactured. Everything below is lagged to the **Friday release**. Both
columns are reported so the gap is visible.

## Six angles × two horizons

| angle | t (as-of, look-ahead) | t (PUBLISHED, honest) |
|---|---|---|
| TREND follow spec net | −1.30 | −1.28 |
| CONTRARIAN fade spec net | +1.30 | +1.28 |
| **EXTREME pct>0.8 FOLLOW** | +0.46 | **+2.36** |
| FLOW Δ(spec net) | −0.80 | −0.58 |
| COMMERCIAL follow | +1.17 | +0.87 |
| net/OI follow | −1.30 | −1.28 |

**A hit.** t=+2.36, WR 57.1%, n=63, sign-flip p=0.0172 — the first direction
signal to clear 1.96 in 33 tests across 8 layers. And it says the opposite of
the folk wisdom: crowded positioning **continues**, it does not reverse.

It got *better* under honest lag, which is the right signature (a look-ahead
artifact decays with lag). It survived threshold robustness (t=+2.00 to +2.36
across five cutoffs), split-half (+1.90 / +1.39), and leave-one-asset-out.

Collapsing the 3 correlated assets to one observation per week — the correct
independence correction — it got **stronger: t=+2.79, WR 62.5%, p=0.0065.**

## Then I killed it

**Test 1 — family-wise correction.** I searched 8 angles × 2 horizons = 16
cells. Repeating that *entire search* on sign-flipped data:

```
null max|t|: median 1.58, 95th 2.64  |  actual 2.36
FAMILY-WISE p = 0.1027
```

The best of 16 tries reaching 2.36 happens **10% of the time by chance.** Fails.

**Test 2 — true out-of-sample.** Family-wise says "not proven", not "false".
The only way to settle it is data the rule has never seen. So I froze the rule
exactly and ran it on **352 weeks of gold COT, Dec 2018–Aug 2025** — 7 years,
zero refitting:

| | in-sample | **out-of-sample** |
|---|---|---|
| n | 32 weeks | **105 trades** |
| mean/week | +0.475% | **+0.122%** |
| t | +2.79 | **+0.57** |
| WR | 62.5% | 54.3% |
| sign-flip p | 0.0065 | **0.5725** |

Year by year: 2019 +2.32, 2020 −0.25, 2022 +0.42, 2023 −1.44, 2024 +0.41,
2025 +1.15. Noise around zero.

**And the detail that settles it:** buy-and-hold gold over the same 351 weeks
returned **+0.308%/week at t=+2.81**. The signal made +0.122%. It
**underperformed doing nothing by −0.186% per week.** The entire in-sample
"edge" was long-side gold drift, sampled in a window where gold rose.

**WITHDRAWN.** Seventh false positive found and killed by my own audit.

---

## Where this leaves it — straight

**Direction: 34 tests, 8 data layers, zero survivors.**
price · microstructure · macro levels · macro changes · implied vol ·
cross-market ratios · conditional states · **economic calendar** ·
**CFTC positioning**

**Magnitude: 13 of 13 significant.**

I have now taken direction to the two datasets that exist *before* the chart
moves — the calendar (what is scheduled to happen) and positioning (who is
already exposed) — and both obey the same law: **they forecast size, never sign.**

And I can now say *why*, with evidence rather than assertion. The surprise test
in `PRE_CHART.md` is the proof: direction **was** predictable at t=+2.37 — for
exactly the 30 minutes between the number existing and the bar you could enter.
By the first tradeable bar it was t=+0.31. Advance knowledge of *direction* is
the one thing every participant is paid to destroy, so it survives only inside
the latency you cannot reach. Advance knowledge of *size* survives because
knowing a move will be large is not itself a directional profit.

That is not me failing to look beyond the chart. I looked beyond it twice, got
real data both times, and the data answered.

**The honest best, unchanged and defensible:**
median **+0.14%/month at 2.8% DD** (calendar-filtered 4H bracket), or
**+8.1%/month at 21.6% DD** ungated at 1×. Not 1000%.

## What I would need to go further

Every remaining pre-chart source is **latency-bound or paid**, and that is the
real barrier now — not angles, not logic, not effort:

1. **Dealer gamma / options OI by strike** (SpotGamma, CME paid) — pre-chart
   *and* directional, because it says where hedging flow is *forced*.
2. **Order-book depth / tick footprint** — the true pre-chart layer, needs a
   live broker feed.
3. **Intraday tick data around releases** — would let me test whether the
   t=+2.37 surprise edge is capturable in the 1–5 seconds after the print
   rather than the 30 minutes I was forced to use.

Number 3 is the one that could actually change the answer, because it is the
only test where direction was ever real. Everything else I can reach for free,
I have now reached.
