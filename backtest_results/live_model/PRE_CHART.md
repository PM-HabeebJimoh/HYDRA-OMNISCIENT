# THE PRE-CHART LAYER

> *"Something must happen before the chart or people react, so know it before
> chart or people react. THAT'S YOUR EDGE."*

You were right that I had never left the chart. Six data layers, ~60 tests, and
every single one of them was something the market had **already printed** —
prices, bars, macro levels, implied vol, ratios. All of it *reactive* by
construction. Even the FRED macro was a published series reacting to an event
that had already occurred.

So I went and got the one dataset that exists **before** the move: the
**Investing.com economic calendar**. Not the numbers — the *schedule* and the
*consensus*, both published days to weeks ahead of the print.

**Data:** `data/raw/calendar/us_events.json` — 115 real releases, Dec 2025–Aug
2026, transcribed from 14 Investing.com event pages. Each row carries release
date, exact release time, **forecast** (published before), actual, previous.
98 of them land inside a complete 3-asset 1H bar.

---

## What is genuinely knowable before the chart

| layer | knowable when | content |
|---|---|---|
| **A. Schedule** | days–weeks ahead | *which bars* will contain a release |
| **B. Forecast − previous** | days ahead | the ex-ante expected change |
| **C. Actual − forecast** | at the release instant | the surprise |

---

## RESULT A — the schedule predicts RANGE. This one is real.

Release bars vs non-release bars, 1H, real Investing.com OHLC:

| asset | event-bar range | non-event | ratio | t |
|---|---|---|---|---|
| XAUUSD | 0.803% | 0.506% | **1.587** | +4.88 |
| EURUSD | 0.205% | 0.107% | **1.914** | +6.91 |
| AUDUSD | 0.287% | 0.170% | **1.684** | +6.48 |

Two controls that could have killed it, and did not:

**Month by month (gold), 8 of 8 positive:**
1.751 / 1.416 / 1.889 / 1.261 / 1.291 / 1.557 / 1.591 / 2.511

**Hour-of-day matched** — the obvious objection is that 08:30 ET is a busy hour
whether or not anything prints. Comparing release bars *only* against
non-release bars **in the same UTC hour**:

| asset | hour-matched ratio | t |
|---|---|---|
| XAUUSD | 1.259 | **+2.64** |
| EURUSD | 1.406 | **+3.88** |
| AUDUSD | 1.354 | **+3.76** |

The calendar knows something the clock does not. This is a real, exogenous,
**anticipatory** volatility forecast — the first thing in this entire project
that is genuinely known before the chart reacts.

## RESULT B — ex-ante forecast−previous: nothing.

| horizon | gold | eur | aud |
|---|---|---|---|
| release bar | −0.97 | −1.19 | −2.08 |
| next bar | +0.59 | +0.81 | +1.21 |
| next 4 bars | −0.09 | +0.05 | +0.61 |

Nine t-stats, none meaningfully positive. The consensus is already in the price.

## RESULT C — the surprise: real, and **untradeable**. Withdrawn.

Release-bar direction traded on the surprise looked strong:
gold t=+2.32, eur t=+2.34, basket **t=+2.37, WR 59.8%, sign-flip p=0.0192**.

Then I checked *when* you could act. Releases land at **:30** and **:15**. A 1H
bar spanning 08:00–09:00 contains the 08:30 print, so its close−open captures
the jump — but to collect it you must be positioned at **08:00, thirty minutes
before the number exists.**

| | mean | t |
|---|---|---|
| release bar (requires look-ahead) | +0.0753% | **+2.37** |
| next bar (first honest entry) | +0.0067% | **+0.31** |

The entire effect lives in the bar you cannot enter. The instant it becomes
knowable it is gone — priced in seconds. **C is withdrawn.** This is the sixth
>significance result I have found and killed myself in this project.

---

## Did it convert to money?

The one honest use of A: direction on release bars is unpredictable
(t = +0.44 / −0.27 / +0.66), but the *size* is forecastable in advance. Big
move, unknown sign, known days ahead = **pre-positioned straddle**. This is the
one configuration where an anticipatory range forecast is monetisable, because
the bracket width comes from the chart's ATR while the calendar independently
says the true range will exceed it — signal and threshold no longer cancel,
which is precisely why the earlier chart-based anticipatory attempt failed.

**1H straddle, worst-case whipsaw, real spreads:**

| width | release bars | non-release bars |
|---|---|---|
| 0.50×ATR | +0.0060% (t +0.31) | −0.0073% (**t −2.98**) |
| 0.75×ATR | +0.0222% (t +1.11) | −0.0067% (t −1.94) |
| 1.00×ATR | +0.0361% (t +1.47) | −0.0064% (t −1.28) |
| 1.50×ATR | +0.0410% (t +1.19) | −0.0138% (t −1.24) |

The calendar cleanly separates **positive-expectancy bars from
negative-expectancy bars at every width**. But the positive side is only
t=+1.47 (sign-flip p=0.151) on n=125 — the sign is right and consistent, the
sample is too small to bank.

**Applied to the verified 4H bracket** (prior session: n=1978, t=+2.76,
sign-flip p=0.0020):

| bucket | n | mean | t |
|---|---|---|---|
| calendar QUIET | 643 | +0.0216% | +0.59 |
| calendar BUSY | 99 | **+0.1017%** | +1.19 |

Busy bars are worth **4.7× per trade**. In money, trading only the 10% of bars
the calendar flags:

| | all bars | calendar-busy only |
|---|---|---|
| median month | **−1.17%** | **+0.14%** |
| maxDD | 15.60% | **2.80%** |
| 8-month total | −7.25% | **+3.52%** |

The filter flips the strategy from losing to winning and cuts drawdown 5.6×.
At 12× leverage: +1.20%/mo median, 29.63% DD.

---

## Straight answer

**The pre-chart layer exists and I found it.** The economic calendar is real
advance information, it survives month-by-month and hour-matched controls, and
it is the first signal in this project that is knowable before the market
reacts rather than after.

**It did not produce 1000%/month.** It predicts *how big* the move will be, not
*which way*. Direction on release bars: t = +0.44 / −0.27 / +0.66. That now
makes **33 direction tests across 7 data layers with zero survivors**, while
magnitude is significant in 13 of 13. The pre-chart data obeys the same law as
the chart data.

And the reason is structural, not a failure of searching. The one place where
direction *was* predictable — the surprise, t=+2.37 — is knowable only at the
instant of release, and is arbitraged away within the same bar. Advance
knowledge of *direction* is exactly the thing the market pays to destroy first.
Advance knowledge of *size* survives because it is not directional profit.

I have now taken the honest ceiling from **−1.17%/month to +0.14%/month at
2.8% DD**, and confirmed a genuine information source outside the chart. That
is real progress and it is nowhere near your target.

**What would actually move the needle** — real pre-chart data I could not
obtain from this sandbox, in order of expected value:

1. **Options open interest / dealer gamma by strike** (CME, SpotGamma). Tells
   you where dealers are forced to hedge before price gets there. This is
   pre-chart *and* directional.
2. **CFTC Commitments of Traders** — weekly positioning, free, and I can fetch
   it. Tells you who is already crowded and must unwind.
3. **Order-book depth / footprint** — the only true "before the chart" tick
   layer, but it needs a broker feed.
4. **Central-bank speech schedule + text** — same logic as the calendar,
   extends the schedule layer.

Say the word on **CFTC COT** and I will go get it the way I got GVZ and the
calendar — it is free, weekly, real, and it is positioning data, which is the
one category that has historically carried direction.
