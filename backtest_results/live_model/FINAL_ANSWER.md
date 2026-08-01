# Is that all? — the answer in WR, DD and monthly ROI

## The one surviving edge, in your three metrics

4H volatility bracket. n=1978, t=+2.76, sign-flip null **p=0.0020**, move-size
gate correct, split-half strengthens. Worst-case whipsaws, real spreads.

| leverage | **WR** | **median monthly ROI** | best mo | worst mo | **max DD** | 8-month |
|---:|---:|---:|---:|---:|---:|---:|
| 1.0× | 49.0% | +8.1% | +57.8% | −16.2% | **21.6%** | +109.6% |
| **2.4×** | **49.0%** | **+17.9%** | +189.1% | −35.8% | **45.1%** | +417.6% |
| 4.9× | 49.0% | +29.0% | +678.4% | −62.3% | 72.6% | +1,680.2% |
| 9.8× | 49.0% | +24.2% | +3,840.2% | −89.6% | 95.3% | +4,797.9% |
| 15× | 49.0% | **−10.4%** | +13,537.7% | −98.4% | 99.6% | +1,486.0% |
| 20× | 49.0% | **−47.9%** | +22,571.2% | −99.9% | 100.0% | **−70.2%** |

**Note rows 5 and 6: past 9.8× more leverage makes the median month NEGATIVE.**
That is the growth-optimum wall. There is no leverage setting that reaches your
target — the curve turns down before it gets there.

## Against your target

| metric | target | achieved (2.4×) | gap |
|---|---|---|---|
| WR | >80% | **49.0%** | +31pp |
| monthly ROI | >1000% | **+17.9%** | **56×** |
| max DD | <8% | **45.1%** | 5.6× |

## Win rate is free — do not use it as a goal

WR is set by the stop/target ratio, not by skill:

| stop:target | WR | expectancy on a fair walk |
|---|---:|---|
| 1:1 | 50.0% | ~0 |
| 2:1 | 66.7% | ~0 |
| **4:1** | **80.0%** | **~0** |
| 9:1 | 90.0% | ~0 |

**I can give you WR 90% tomorrow with a 9:1 stop. It earns nothing.** Any system
advertising 80%+ WR is telling you its stop geometry, not its edge.

## Is that all? Here is the full inventory

**Direction — 10 independent attacks, all dead:**

| attack | scope | result |
|---|---|---|
| direct momentum | 3 TF | ~50%, t −0.88 to +0.49 |
| cross-sectional rank | 3 assets | t=−1.86 |
| lead-lag | 6 pairs | gross \|t\|<1.6, retracted |
| acceleration | 3 TF | t=+0.81 |
| hour-of-day | 24 slots | noise |
| day-of-week | 5 slots | noise |
| combinatorial | 12 cells | best t=−1.94 |
| ML walk-forward | 30+ features | 48–55% after leak fix |
| rule grid | 2,016 configs | fails noise null |
| causal filters | 33 tests | +4.37pp vs +5.10pp noise median |

**Structure — 6 attacks, all dead:**

| attack | scope | result |
|---|---|---|
| leverage sweep | 259,200 configs | MAR flat then falls, 0 above 1000% |
| basket swap | 196 baskets | fails selection null p=0.075 |
| V3 cap | −2% basket limit | absorbs $7.0m of real losses = fake |
| V82 port | 8 months | +988% but params fitted in-sample |
| 36-stream Kelly | 73,400 trades | concurrency error, N_eff 7.88 not 36 |
| covariance opt | Σ⁻¹μ | 8.62 in-sample → **0.25 out** |

## The one genuinely untested lever, and its ceiling

Run the verified bracket across uncorrelated instruments. Measured cross-asset
efficiency (gold/EUR/AUD + SPX + BTC) = **0.49 per instrument**.

| instruments | N_eff | portfolio Sharpe | median monthly ROI at ~8% DD |
|---:|---:|---:|---:|
| 3 | 1.5 | 3.38 | 17.8% |
| 20 | 9.8 | 8.73 | 45.9% |
| 65 | 31.8 | 15.73 | 82.8% |
| **100** | **49.0** | **19.52** | **~103%** |

**Even at 100 instruments this reaches ~100% a month at 8% DD — not 1000%.**

## The straight answer

**Yes, that is all.** Not because I stopped looking — because sixteen independent
attacks converge on the same place. The honest ceiling for a t=+2.76 edge is a
few hundred percent a *year* at survivable risk, or ~100%/month at 8% DD with a
100-instrument book.

**>1000% monthly at <8% DD requires MAR 125 — roughly 25–40× the best track
record in financial history.** Nothing in 8 months of gold/EUR/AUD comes within
two orders of magnitude of it, and I have now shown you five separate times what
it looks like when a number *appears* to get there: a look-ahead bug, a −2% cap
that deletes real losses, in-sample parameter fitting, a concurrency error, and a
36×36 covariance overfit. Each one dissolved when tested.

What you have that is real: **a volatility edge that passes every gate I know how
to run, paying +18%/month at 45% DD or +8%/month at 22% DD.** That is a genuine
result. It is not the one you asked for.

Reproduce: `research.final_metrics`, `research.whats_left`
