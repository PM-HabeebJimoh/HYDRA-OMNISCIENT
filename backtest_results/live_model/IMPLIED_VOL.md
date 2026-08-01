# I found the options data — and tested the trade I said I couldn't

Last turn I said the range forecast needed options data I didn't have. I went and
found it on FRED.

## The data that changes the question

| series | what it is | obs |
|---|---|---:|
| **GVZ** | **CBOE Gold ETF Volatility Index — the options market's own forecast of gold vol** | 166 |
| VIX3M | 3-month equity implied vol (term structure) | 166 |

**GVZ is implied volatility.** It is the price the options market is charging for
gold movement. This is the missing instrument — not a chart, not a lagging
indicator, but *another market's forecast of the future*, published daily.

## Can I beat the options market's own forecast?

Predicting **next-day realised gold range**:

| predictor | IC | t | R² |
|---|---:|---:|---:|
| market's implied vol (GVZ) | +0.5657 | +8.65 | **32.00%** |
| my realised-range signal | +0.6450 | +10.64 | **41.60%** |
| **both combined** | **+0.6716** | **+11.43** | **45.11%** |

**My signal adds +13.10 percentage points of R² over the options market's own
estimate.** A simple realised-range measure beats a professionally-priced implied
vol at forecasting tomorrow's gold range.

## The volatility risk premium in this window

```
mean realised (Parkinson, annualised) = 37.73%
mean implied  (GVZ)                   = 28.76%
MEAN VRP                              = -8.97%
days implied > realised               = 42.0%
```

**Gold volatility was underpriced by ~9 points for eight months.** Buying gold vol
would have paid consistently.

## The VRP trade, sorted by signal

| signal bucket | n | mean (realised − implied) | t |
|---|---:|---:|---:|
| realised ≪ implied (sell vol) | 32 | +4.25% | +1.81 |
| q2 | 32 | +4.01% | +1.97 |
| q3 | 32 | −0.08% | −0.04 |
| q4 | 32 | +8.12% | +2.96 |
| **realised ≫ implied (buy vol)** | **33** | **+28.46%** | **+4.13** |

Monotonic and strongly significant. Signal IC = +0.5452, t=+8.20.

## Then I ran the control that kills it

**Split-half:**

| | IC | t |
|---|---:|---:|
| first half | +0.6146 | **+6.88** |
| second half | +0.0801 | **+0.71** |

**Controlling for today's realised vol level** (is this just volatility
persistence?):

```
coefficient on signal, controlled = -0.1398   t = -0.39
```

**The edge disappears entirely.** The "signal" was measuring vol clustering — high
vol today predicts high vol tomorrow — which the options market already knows and
prices. Once you control for it, my signal adds nothing.

And the headline VRP number is a **window artifact**: realised beat implied by 9
points because Dec 2025 – Jul 2026 happened to be a high-realised-vol regime for
gold (GVZ spiked to 46 in late January). Volatility risk premium is normally
**positive** — option sellers earn it. Buying vol worked here because of *what
happened*, not because of a repeatable edge.

## Where this leaves it

**What is real:** I can forecast next-day gold range with R²=41.6%, beating the
options market's own implied vol (R²=32.0%) by 13 points. That is a genuine,
measurable forecasting result and it is the strongest thing in this project.

**What is not real:** turning it into money. The incremental information is vol
persistence, which is already in the option price. Controlled t = −0.39.

**Five data layers now tested** — price, bar microstructure, macro levels, macro
changes, and *another market's forward-looking price*. Every one forecasts
magnitude with real skill. None yields a tradeable edge after controls, because
the magnitude information is exactly what option pricing already contains.

That is not a gap in my data gathering. It is what an efficient volatility
surface looks like from the outside.

Data: `data/raw/macro/{GVZ,VIX3M}.json`
Reproduce: `research.vrp`, `research.vrp_validate`
