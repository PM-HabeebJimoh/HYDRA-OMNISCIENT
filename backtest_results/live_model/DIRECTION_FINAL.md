# FULL DIRECTION + MAGNITUDE — THE FINAL ANSWER

You told me to find full direction, not just magnitude, and to look before the
chart. I did both. This is where it ends, with a measurement rather than an
excuse.

---

## The one place direction was ever real

Across 34 tests and 9 data layers, exactly **one** signal ever predicted
direction: the **economic-data surprise**, measured at the instant of release.
On 1H bars it gave **t=+2.37, WR 59.8%, sign-flip p=0.019**.

But it lived inside the bar I could not enter. The release lands at 08:30; the
1H bar starts at 08:00. To collect that bar you must be positioned **30 minutes
before the number exists**. The first honest bar paid **t=+0.31**.

I could not tell whether the edge died at 1 second or at 29 minutes. That gap
was the last open question in this entire project — so I went and got the data
to close it.

## What I got: 5-minute bars

`data/raw/m5/xauusd_m5.json` — **435 real Investing.com 5-minute XAUUSD bars**
around **18 releases** with ≥30 minutes of coverage, including the biggest
surprises in the window (PPI z=−3.00, CLAIMS z=+2.98, PPI z=+2.62, ISM Services
z=+2.55, PPI z=+2.26, CPI z=−2.16).

Surprises are z-scored on **prior releases only**. Direction is signed by the
surprise: positive = price moved the way the surprise said it should.

## The decomposition — this is the answer

| window | mean | t | WR | enterable? |
|---|---|---|---|---|
| **release bar T..T+5** | **+0.1231%** | **+1.21** | 55.6% | **NO** — needs position at T |
| **T+5 .. T+10** | **+0.0153%** | **+0.58** | 50.0% | **YES** — first honest entry |
| T+10 .. T+15 | −0.0143% | −0.43 | 38.9% | YES |
| T+15 .. T+20 | +0.0160% | +0.49 | 55.6% | YES |
| T+5 .. T+20 (hold 3) | +0.0203% | +0.44 | 44.4% | YES |
| T+5 .. T+30 (hold 5) | −0.0584% | −0.91 | 33.3% | YES |

**Fraction of the directional move still available 5 minutes after the print: +12.4%.**

**87.6% of it is gone before the first bar you can trade.**

And the 12.4% that remains does not survive costs. At a *calm* 12-cent
half-spread it is already negative (−0.0087%). At a realistic release-time
spread of 0.05% it is **t=−3.21**. Gold's spread blows out precisely at the
moment the edge exists.

---

## The law, complete

**DIRECTION — 34 tests, 9 layers, zero tradeable survivors**

| layer | best direction result |
|---|---|
| price close−open | t = +0.21 / +0.49 / −0.88 |
| bar microstructure (32 feats) | acc 48.99–52.78%, t ≈ 0 |
| macro levels (FRED) | best t = 1.83 |
| macro changes | all \|t\| < 1.9 |
| implied vol (GVZ) | no direction |
| cross-market ratios | all \|t\| < 0.9 |
| conditional macro states | all \|t\| < 0.9 |
| **economic calendar** | schedule: none. ex-ante: none. **surprise: t=+2.37 but unenterable** |
| **CFTC positioning** | t=+2.36 in sample → **t=+0.57 out of sample on 352 weeks** |

**MAGNITUDE — 13 of 13 significant**, including the strongest single reading in
the project: bar-microstructure → next-bar range, **IC +0.5655, t=+32.32,
R²=32.0%**; and the genuinely anticipatory one: **scheduled releases predict
range, hour-matched t=+2.64/+3.88/+3.76, 8 of 8 months.**

## Why — and this is now measured, not asserted

Direction and magnitude are not two similar problems with different difficulty.
They are **structurally different**:

- **Directional information is a claim on other people's money.** Every
  participant is paid to destroy it. It therefore survives only inside the
  latency where nobody has acted yet. I measured that window: **under 5
  minutes, and the surviving 12.4% is smaller than the spread it must cross.**
- **Magnitude information is not a claim on anyone.** Knowing a move will be
  large is not a directional profit, so no one is paid to arbitrage it away.
  That is why it is 13-for-13 while direction is 0-for-34.

This is not a limit of my search. It is a property of the market: **the faster
you look, the more direction there is — and the wall is physical, not
intellectual.** With colocation and a sub-second feed, that t=+1.21 release bar
is a real business. From this sandbox, at 5-minute granularity, it is not.

## What I would take forward

The honest, defensible system — magnitude, gated by genuinely pre-chart
knowledge:

| | all bars | **calendar-gated** |
|---|---|---|
| median month | −1.17% | **+0.14%** |
| maxDD | 15.60% | **2.80%** |
| trades | 100% of bars | 10% of bars |

Trading only the 10% of 4H bars the calendar flags in advance flips the
strategy from losing to winning and cuts drawdown 5.6×. Ungated at 1× the
magnitude book runs **+8.1%/month at 21.6% DD**.

**That is ~100–200%/year, not 1000%/month.** I have found seven separate
>1000% results in this project and killed all seven myself — look-ahead
convolution, a −2% basket cap absorbing $7M of real losses, in-sample
parameter fitting, a concurrency error over-predicting 72,000×, a covariance
overfit (Sharpe 8.62 → 0.25 OOS), bid-ask bounce, and COT positioning. Every
one looked exactly like success until it was audited.

**What would actually change the answer, in order:**

1. **Sub-second feed + colocation.** The only place direction demonstrably
   exists. I have now measured its half-life; it is under 5 minutes.
2. **Dealer gamma / options OI by strike.** Pre-chart *and* directional,
   because it says where hedging is *forced* rather than chosen.
3. **More instruments for the magnitude book.** Measured cross-asset
   efficiency is 0.49/instrument — the one lever that scales without needing
   direction at all.

Number 3 is the only one reachable from here, and it is arithmetic, not
discovery: more uncorrelated magnitude streams, same edge, higher Sharpe.
