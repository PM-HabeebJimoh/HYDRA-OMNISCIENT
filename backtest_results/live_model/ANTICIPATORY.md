# The anticipatory model — built, and what it actually proved

You were right about the diagnosis: I had only ever used two numbers per bar
(close−open for direction, high−low for range). Everything else in the data I
threw away.

## The layers I extracted

| layer | features built |
|---|---|
| **INVISIBLE** | close location in range (CLV), body/range ratio |
| **HIDDEN** | wick skew — which side got rejected, implying who hit their extreme first |
| **SCATTERED** | cross-asset dispersion of CLV and body — meaningless per asset, structural across three |
| **NOISY** | overnight gap (open vs prior close) — I had only ever used *within*-bar |
| **DISREGARDED** | upper wick, lower wick, separately rather than netted |

Plus trailing realised vol and vol-of-vol per asset. **32 features**, all causal.

## Individually they are weak — as expected

Best single-feature t-stats: DAILY body/range +1.68, 1H body dispersion +2.44,
everything else under 1.5. Individually, noise.

## Combined, walk-forward, leak-free — this is the finding

| TF | target = **DIRECTION** | target = **RANGE** |
|---|---|---|
| DAILY | acc 52.78%, t=+0.25 | IC **+0.3881**, t=+4.34, **R² 15.1%** |
| 4H | acc 48.99%, t=+0.08 | IC **+0.4802**, t=+13.32, **R² 23.1%** |
| 1H | acc 50.92%, t=−1.74 | IC **+0.5655**, t=+32.32, **R² 32.0%** |

**Out-of-sample R² of 32% predicting the next bar's range.** That is a genuine
anticipatory model — it knows what is coming before it happens. t=+32.32.

**And the same 32 features predict direction at 48.99–52.78%, t≈0.** The hidden
layers you described are real and they carry enormous information — **but all of
it is about magnitude, none about direction.**

## Then I tried to trade the forecast — and it failed

Logic: forecast says big range → place a bracket; forecast says small → stand aside.

| forecast filter | n | WR | mean | t |
|---|---:|---:|---:|---:|
| **4H** all bars | 1203 | 50.71% | +0.0410% | **+2.44** |
| 4H top 50% | 574 | 51.05% | +0.0594% | +2.12 |
| 4H top 30% | 323 | 51.08% | +0.0743% | +1.88 |
| 4H top 15% | 167 | 49.10% | +0.0525% | +0.84 |
| 4H **top 5%** | 52 | 40.38% | **−0.0609%** | −0.47 |
| **1H** all bars | 4167 | 46.34% | +0.0050% | +0.92 |
| 1H top 5% | 233 | 42.06% | **−0.0409%** | −1.03 |

**The better the forecast, the worse the trade.** Filtering to the top 5% of
predicted-range bars *destroys* the edge — it goes negative.

## Why. This is the part that matters.

The forecast works. R²=32% is real and large. But **a range forecast is not an
edge, because the market prices it.**

When my model predicts a big move, so does everyone else — the same information
is in the same bars. A big *predicted* range means a wide bracket must be placed
(the stops sit further out), so the move has to be even bigger to pay. The
forecast and the required threshold rise together and cancel.

This is the volatility-risk-premium result: **predictable volatility is not free
money; it is already in the price of the straddle.** To monetise a vol forecast
you need an instrument whose price is set by *someone else's* vol estimate — an
option. With spot brackets you are quoting against yourself.

## Where this leaves the target

| | |
|---|---|
| best honest edge | 4H bracket, **all bars**, t=+2.44 |
| WR | ~50% |
| median monthly ROI | +18% at 2.4×, +29% at 4.9× |
| max DD | 45% / 73% |

**>700% monthly at low DD is not reachable from here.** The anticipatory layer is
real — R² 32% is a serious forecast — but it forecasts the one thing that spot
brackets cannot monetise.

## What I would do next, concretely

The forecast has commercial value in exactly one place: **options**. If the model
predicts realised range with R²=32% and an option is priced off implied vol, the
trade is buy straddles when forecast > implied, sell when forecast < implied. That
is the instrument this signal was built for.

I cannot test it here — I have no options data, no implied vol surface. That is a
data acquisition problem, not a modelling one, and it is the honest next step
rather than another leverage sweep on spot.

Reproduce: `research.hidden`, `research.combine`, `research.anticipate`
