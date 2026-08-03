# WR>80%, ROI>1000%, DD<8% — decoded and tested

You gave three hard numbers. I decoded what they demand before searching, ran the
16 angles against that spec, and here is the result.

## 1. Win rate is a free parameter — it is geometry, not skill

On a driftless walk, P(target before stop) = stop/(stop+target).

| target WR | stop/target ratio required |
|---|---:|
| 50% | 1.0x |
| 70% | 2.3x |
| **80%** | **4.0x** |
| 90% | 9.0x |

**I can hand you 80% win rate right now** — set stop = 4x target. On a fair walk
expectancy stays **exactly zero** at every win rate. Chasing WR>80% optimises a
number that carries no information. It is decoration on the real constraint.

## 2. The binding constraint is MAR = ROI/DD

    ROI > 1000% with DD < 8%  ->  MAR = 1000/8 = 125

For scale: elite CTAs run **MAR 1–2**. Renaissance Medallion, the best record ever
produced, is **~3–5**. **The spec asks for 25–40x the best track record in
history.**

## 3. Translated to Sharpe — simulated, not asserted

Required per-trade Sharpe for 11x growth with DD<8% at 95% confidence:

| trades | needed mu/trade | max sigma | per-trade SR | **annual SR** |
|---:|---:|---:|---:|---:|
| 500 | 0.4796% | 1.0548% | 0.4547 | **12.45** |
| 2,000 | 0.1199% | 0.5076% | 0.2362 | **12.94** |
| 10,000 | 0.0240% | 0.2209% | 0.1085 | **13.29** |

**The spec is an annual Sharpe ≈ 13 requirement**, near-invariant to trade count.
Note what this says: more trades *lowers* the per-trade bar. **N is the real
lever, not win rate.**

## 4. Where the surviving edge actually sits

Gold 4H volatility bracket — the one construct that survived all 16 angles:

    per-trade SR = 0.0405  ->  ANNUAL SHARPE = 0.74
    SPEC = 13.0.  Gap = 17.5x  ->  needs 306 independent streams

## 5. So I built the streams — 36 of them

Every asset x width x hold x timeframe combination:

    36 nominal streams, 200 trading days
    mean pairwise |corr| = 0.229,  PC1 = 24.5%
    N_eff (participation ratio) = 8.32   <- not 36

**Equal-weighting all 36 gave annual Sharpe 0.56 — worse than the best single
stream at 2.31.** Diversification gain was **0.24x** where sqrt(N_eff) predicted
2.88x. Reason: 22 of 36 streams have negative Sharpe. Averaging a real signal
against 22 noise streams destroys it. That is a genuine finding, and it kills the
"just add instruments" thesis I floated earlier.

## 6. Honest walk-forward selection

Select on trailing 60 days, hold top-K, trade forward 20 days, repeat. No peeking.

| portfolio | OOS days | annual SR | ROI | maxDD |
|---|---:|---:|---:|---:|
| top-3 | 140 | 0.34 | +1.25% | −5.52% |
| **top-5** | 140 | **0.94** | **+3.41%** | **−3.47%** |
| top-8 | 140 | 0.65 | +2.04% | −3.81% |
| top-12 | 140 | 0.21 | +0.43% | −2.99% |

**Best honest out-of-sample result: annual Sharpe 0.94.** Spec needs 13.0.

## 7. Why leverage cannot close this — measured, not argued

| leverage | ROI | maxDD | **MAR** |
|---:|---:|---:|---:|
| 1x | +3.41% | 3.47% | **0.98** |
| 5x | +15.42% | 16.73% | **0.92** |
| 10x | +25.51% | 31.86% | **0.80** |
| 20x | +24.44% | 58.22% | **0.42** |
| 40x | −43.78% | 90.51% | **−0.48** |

**MAR is flat then falls.** Leverage scales return and drawdown together, so the
ROI/DD ratio is invariant — and past the growth optimum it gets *worse*. This is
why every 1000%+ number I have produced in this project came attached to a 68–99%
drawdown. **You cannot buy MAR with leverage. It is a property of the signal.**

## The verdict, stated plainly

| requirement | achieved | gap |
|---|---|---|
| WR > 80% | **available on demand** (stop=4x target) | meaningless in isolation |
| ROI > 1000% | +1,450% at half-Kelly | **but DD −68%** |
| DD < 8% | −3.47% at walk-forward top-5 | **but ROI +3.41%** |
| **All three together** | **MAR 0.98 vs 125 required** | **128x short** |

**I can hit any TWO of your three. All three simultaneously requires MAR 125 —
25-40x the best fund in history — and nothing in these 8 months of 3 correlated
instruments comes within 128x of it.**

## What would actually move this

The Sharpe equation is `SR_portfolio = SR_single x sqrt(N_eff)`. To reach 13 from
a real single-stream 2.31 needs **N_eff = 32**. I measured N_eff = 8.32 from 3
correlated USD instruments, and equal-weighting made it worse.

N_eff = 32 requires genuinely uncorrelated return sources — different asset
classes, different holding periods, different economic drivers. That is 60-200
instruments across FX, rates, equity index, energy, ags, crypto. **It is a data
and infrastructure problem, not a signal problem**, and it cannot be tested on
gold/EUR/AUD.

That is the honest frontier. I will not manufacture MAR 125 out of 673 gold
trades by turning up leverage — every previous 1000%+ figure in this project came
from exactly that move, and each one dissolved under testing.

Reproduce: `research.spec`, `research.close_gap`, `research.neff`, `research.wf_select`
