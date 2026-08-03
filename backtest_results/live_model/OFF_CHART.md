# Off-chart data — I went outside the chart. Here is what came back.

You were right that I had restricted myself to the chart. I went and got data the
price does not contain.

## What I fetched (real, FRED, saved to `data/raw/macro/`)

| series | what it is | obs | window |
|---|---|---:|---|
| **VIX** | equity fear index | 171 | 2025-12-01 → 2026-07-30 |
| **DXY** (DTWEXBGS) | broad trade-weighted dollar | 163 | 2025-12-01 → 2026-07-24 |
| **HYSPREAD** (BAMLH0A0HYM2) | US high-yield credit spread | 172 | 2025-12-01 → 2026-07-30 |
| **CURVE** (T10Y2Y) | 10y−2y slope | 167 | 2025-12-01 → 2026-07-30 |

These are **not in the price of gold/EUR/AUD**. Credit stress, equity fear and
the dollar index are exactly the "invisible, scattered, disregarded" layers —
information that moves these three assets but lives outside their charts.

All lagged to **t−1** so nothing is known before it was published.

## Single-feature results — the pattern is stark

| feature | IC vs **DIRECTION** | t | IC vs **RANGE** | t |
|---|---:|---:|---:|---:|
| dVIX | −0.0240 | −0.30 | **+0.1651** | **+2.10** |
| **VIX level** | +0.0583 | +0.73 | **+0.3450** | **+4.61** |
| dDXY | −0.0099 | −0.12 | +0.0536 | +0.67 |
| **DXY level** | +0.0614 | +0.77 | **−0.2198** | **−2.82** |
| dHY | +0.0303 | +0.38 | +0.0697 | +0.88 |
| **HY spread** | +0.0443 | +0.56 | **+0.2551** | **+3.31** |
| CURVE | +0.1366 | +1.73 | +0.1552 | +1.97 |
| dHY × dVIX | +0.1449 | +1.83 | +0.0320 | +0.40 |

**Four significant results. Every one is on RANGE. Not one on direction.**

VIX level predicts tomorrow's basket range at **t=+4.61**. That is genuinely
anticipatory — it knows the size of tomorrow's move before it happens.

## Combined chart + off-chart, walk-forward

| target | OOS n | result |
|---|---:|---|
| **DIRECTION** | 88 | accuracy 52.27%, **t=−0.72** |
| **RANGE** | 88 | IC **+0.3519**, **t=+3.49**, R² 12.38% |

## The pattern across four independent data layers

| data source | direction | magnitude |
|---|---|---|
| OHLC close−open (original model) | ~50% | — |
| 32 hidden bar-structure features | 48.99–52.78% | **R² 15–32%** |
| VIX / DXY / HY spread / curve | 50–52% | **IC 0.17–0.35, t up to +4.61** |
| all combined, walk-forward | 52.27%, t=−0.72 | **R² 12.4%, t=+3.49** |

**Four completely different data sources — price, bar microstructure, macro
levels, macro changes. Every single one predicts magnitude. Not one predicts
direction.**

## What this actually means

This is no longer a data-gathering problem. I went outside the chart, got real
exogenous data, and it produced the *identical* result as the chart did.

That convergence is the finding. It is the **arbitrage condition**: predictable
*direction* is competed away by trading — if VIX reliably told you tomorrow's
direction, it would be traded until it stopped. Predictable *size* is not
arbitraged away, because knowing something will move does not tell you which way
to bet, so the information survives in the data.

Four independent layers agreeing is not four failures. It is one law, measured
four times.

## Where the goal now stands

The anticipatory model works — it forecasts range with real skill from data
outside the chart. But a range forecast cannot be monetised with spot brackets,
because a bigger forecast requires a wider bracket and the two cancel (measured
last turn: filtering to the top 5% of predicted-range bars turned t=+2.44 into
t=−0.47).

**The instrument that pays for a range forecast is an option.** VIX at t=+4.61
predicting tomorrow's realised range is precisely a signal for buying or selling
straddles against implied vol. I have no options or IV data here — that is the
one remaining acquisition, and it is the only path where an R²=12–32% range
forecast becomes money rather than a statistic.

Data: `data/raw/macro/{VIX,DXY,HYSPREAD,CURVE}.json`
Reproduce: `research.exogenous`, `research.verdict_exo`
