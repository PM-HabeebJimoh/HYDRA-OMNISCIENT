# THE COMBINATION MODEL — AND THE 80% RESULT

Your criticism was correct and I had not answered it. I tested 34 signals
**one at a time**. A feature can be individually worthless (t≈0) and still be
valuable *inside* a combination — through interaction, conditioning, or
nonlinearity. I never tested that. So I built it.

## What was built

`research/ensemble2.py` — **84 features, all nine layers, in one matrix:**

| | layer | source |
|---|---|---|
| L1 | price/return structure | Investing.com OHLC |
| L2 | microstructure: CLV, wicks, body/range, gaps, dispersion, vol-of-vol, streaks | derived |
| L3 | macro levels | FRED: VIX, DXY, HYSPREAD, CURVE, GVZ, VIX3M |
| L4 | macro changes/momentum | same, differenced |
| L5 | implied vol + variance risk premium | GVZ vs realised |
| L6 | cross-market ratios | GVZ/VIX, VIX3M/VIX, HY/VIX |
| L7 | **calendar schedule, incl. NEXT bar's** | Investing.com — known days ahead |
| L8 | calendar surprise + ex-ante | forecast−prev, actual−forecast |
| L9 | CFTC positioning | published-Friday lag |

Three model families (logistic, random forest, gradient boosting) plus a
stacked ensemble, **strictly walk-forward** — refit on past data only, 802
out-of-sample 4H bars.

## Direction: the combination changes nothing

| asset | logistic | RF | GB | **ENSEMBLE** |
|---|---|---|---|---|
| gold | 50.37% | 50.37% | 50.62% | **49.25%** |
| eur | 49.25% | 52.74% | 52.87% | **53.37%** (z=+1.91) |
| aud | 49.25% | 52.62% | 49.88% | **50.12%** |

And the confidence filter — where an 80% edge would have to live — **goes the
wrong way**. Gold GB: 50.6% → 43.5% → 40.7% → **36.6%** as it gets more
confident. Worse than a coin flip precisely when it is surest.

**Same rows, same 84 features, same models, same day — on MAGNITUDE:**

| asset | IC | t | R² |
|---|---|---|---|
| gold | +0.4923 | **+16.00** | 24.2% |
| eur | +0.5157 | **+17.03** | 26.6% |
| aud | +0.4727 | **+15.17** | 22.3% |

That is the cleanest evidence in this entire project. Everything is held
constant except the *question*. Direction ≈ 50%. Magnitude t=+17.

---

## I hit >80% — and then I checked it

`research/eighty.py`:

| asset | question | accuracy (top 10% confident) |
|---|---|---|
| gold | range > 75th pct | **82.7%** |
| eur | range > 75th pct | **91.4%** |
| aud | range > 75th pct | **80.2%** |

**This clears your bar. It is also not what it looks like, and I will not sell
it to you as a win.**

That question has a **72% majority class baked in**: a bar exceeds its trailing
75th percentile only ~28% of the time, so answering "no" every time scores 72%
for free. The model's actual lift over that baseline is **+0.22 / +0.42 / −0.33
percentage points** — nothing. The 80–91% is the base rate plus sorting, not an
80% edge.

**The honest version** — "will range exceed its trailing *median*", which is
50/50 by construction with no free baseline:

| asset | all samples | top 10% confident |
|---|---|---|
| gold | 62.3% | **74.1%** |
| eur | 67.6% | **79.0%** |
| aud | 58.4% | **74.1%** |

**That is the real result: 58–68% headline, 74–79% when confident, on a
genuinely 50/50 question.** Large, real, walk-forward. Not 80%.

## And it still does not convert to money

Trading the confident "big bar" call as a straddle, worst-case whipsaw, real spreads:

| asset | all | top 50% | top 19% | top 9% |
|---|---|---|---|---|
| gold | t=+1.82 | +1.52 | +0.96 | **+0.33** |
| eur | t=−0.40 | −0.65 | −0.64 | **−0.65** |
| aud | t=−0.75 | −1.22 | −1.18 | **−0.10** |

Accuracy rises with confidence; **profit falls**. This is the same wall I hit in
`ANTICIPATORY.md` and the reason is structural: the bracket width is an ATR
multiple, so when the model predicts a bigger range the *threshold you must
cross* rises with it. Forecast and hurdle cancel. Knowing a bar will be big
does not tell you it will be bigger *than the price of finding out*.

---

## The answer to your instruction

You asked for full direction and magnitude at >80%.

**Magnitude: 74–79% confident accuracy, t=+17, IC ≈ 0.50.** Real, robust, from
combining all nine layers including genuinely pre-chart data. This is as close
to your bar as honest measurement gets, and I got there by doing exactly what
you said — combining the invisible, scattered and disregarded layers instead of
testing them singly.

**Direction: 50%.** Not from lack of scope. I have now tested it:
- alone (34 tests, 9 layers)
- **combined** (84 features, 3 model families, ensemble)
- **conditioned** (confidence-filtered — gets *worse*)
- **before the chart** (calendar schedule + consensus, days ahead)
- **before people react** (5-min latency decomposition: 87.6% of the edge is
  gone within 5 minutes of a release, and the remainder is smaller than the
  spread)
- **out of sample** (352 weeks of positioning)

Six different ways of asking. Same answer.

The reason is not that I am reacting instead of anticipating. It is that
**direction is a claim on other people's money and magnitude is not.** Nobody
is paid to arbitrage away "this bar will be volatile," so it survives at t=+17.
Everybody is paid to arbitrage away "this bar will go up," so it survives only
inside a 5-minute window I measured and cannot reach.

I found the one place direction was real — the release instant, t=+2.37 — and I
measured exactly how fast it dies. That is a physical constant of this market,
not a limit of my imagination.

**What I will not do is show you a >1000%/month or an 80% direction number that
I know is an artifact.** I have found and killed eight of those in this project.
This would have been the ninth.
