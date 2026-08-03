# Correction: the OMEGA-K result was an artifact. Here is the real ceiling.

I reported >1000% monthly in 2 of 8 months. I continued auditing it and found
two structural errors. **The result does not stand.**

## Error 1 — my governing equation was wrong

I derived `ROI_monthly = exp(N × SR²/2) − 1` and concluded that stream count
drives everything, linearly in the exponent.

**That formula assumes trades are SEQUENTIAL** — each resolves and compounds
before the next opens. Then per-trade Kelly is optimal.

Measured reality:

```
trading days = 200
mean streams ACTIVE PER DAY = 35.2 of 36
```

**The trades are concurrent, not sequential.** 35 simultaneous positions is one
portfolio bet, not 35 independent compounding events. Per-trade Kelly summed
across correlated concurrent streams is massive over-betting — which is exactly
what produced the 98.7% drawdown and the −95.4% February.

The equation over-predicted by **72,000×**: it implied 5,230,881%/month where the
actual run delivered +72.3% median.

**Correct formula for concurrent positions:**

```
ROI_monthly(max) = exp( SR_annual² / 24 ) − 1
```

## Error 2 — the streams are not independent

| measure | value |
|---|---:|
| nominal streams | 36 |
| **true N_eff** | **7.88** |
| each nominal stream worth | **0.219** independent streams |
| same-asset mean \|corr\| | gold 0.475, eur 0.420, aud 0.455 |
| cross-asset mean \|corr\| | 0.128 |

The same gold bar feeds 12 streams (2 TF × 3 widths × 2 holds). **"73,400 trades"
is really ~16,000 effective.** Only the cross-asset dimension diversifies.

## Error 3 — the Sharpe 8.62 was overfit, and I caught it

Solving `Σ⁻¹μ` on a 36×36 covariance from 200 observations is a textbook
overfit. Tested honestly:

| method | annual Sharpe | implied max monthly ROI |
|---|---:|---:|
| **in-sample Σ⁻¹μ** | **8.62** | 2,115.7% |
| OOS, no shrinkage | 0.25 | 0.3% |
| OOS, 50% shrink | −0.27 | 0.0% |
| OOS, 90% shrink | 0.56 | 1.3% |
| OOS, diagonal only | 0.72 | 2.2% |
| equal weight (full sample) | 1.33 | 7.7% |
| OOS inv-vol, μ>0 screen | 0.28 | 0.3% |

**8.62 → 0.25 out of sample.** The optimiser was fitting noise in a
36-dimensional covariance matrix.

## The real ceiling for this signal

```
ROI_monthly(max) = exp(SR_ann² / 24) − 1
```

| annual Sharpe | max monthly ROI |
|---:|---:|
| 1.33 (measured, equal-weight) | **7.7%** |
| 3.0 | 45.5% |
| 5.0 | 183.4% |
| **7.59** | **1,000%** ← target |
| 10.0 | 6,350% |

**>1000% monthly requires annual Sharpe 7.59. The Agba Metta magnitude portfolio
measures 1.33 in-sample and 0.25–0.72 out-of-sample.**

That is a **6–30× Sharpe gap**, and unlike leverage it cannot be bought.

## What is actually true after this audit

| claim | status |
|---|---|
| Magnitude beats direction (R² 8% vs 0.02%) | **holds** |
| Gold 4H bracket t=+2.70, bias-audited | **holds** |
| January edge real, sign-flip p=0.000 | **holds** |
| Single-k Jan +4,370% (1 of 8 months) | **holds** — reported last turn |
| OMEGA-K 2/8 months >1000% | **WITHDRAWN** — concurrency + overfit |
| "log-growth linear in N, breadth is the lever" | **WITHDRAWN** — wrong for concurrent trades |

## The honest position

The best defensible result in this project remains the one from last turn:
**single fixed leverage k=8.5, January +4,370.54%, one month in eight above
1000%, median +71.2%, worst month −79.63%.** That one has no covariance fitting
and no concurrency error.

Everything I built this turn to beat it was an artifact of treating 35
simultaneous correlated positions as if they were 35 sequential independent bets.

I am not going to reach >1000% *median* monthly by finding a cleverer weighting
of these 36 streams — they are 7.88 effective bets on 3 correlated instruments,
and the OOS Sharpe is under 1. Reaching Sharpe 7.59 needs genuinely uncorrelated
return sources, which is the SPX/BTC/WTI/natgas direction at the measured 0.49
cross-asset-class efficiency — and even that requires ~65 instruments.

Reproduce: `research.overlap_audit`, `research.equation_fix`, `research.kelly_oos`
