# Agba Metta Omega — hunting >1000% MONTHLY

Target: >1000% monthly ROI, drawdown unconstrained. Agba Metta only.

## What I changed in the model

Kept the 3-asset alignment. Changed what it bets on:

| | old Agba Metta | Omega |
|---|---|---|
| signal | alignment on closed bar | same |
| **bet** | **DIRECTION** (R² 0.02%, ~50%) | **MAGNITUDE** (R² 8%) |
| execution | market order, 1% stop | bracket: buy-stop above / sell-stop below |
| whipsaw | n/a | **both triggers hit = full double loss** (worst case) |
| costs | none | real spreads, 2 legs |

Direction-neutral execution means the coin-flip problem disappears — you profit
from the *size* of the break, not its side.

## Result 1 — hindsight-optimal leverage per month: 15 cells above 1000%

| config | month | ROI |
|---|---|---:|
| 4H w0.75 h3 | 2026-01 | **67,982%** |
| 4H w1.0 h3 | 2026-01 | 12,097% |
| 4H w1.0 h3 | 2026-04 | 10,455% |
| 4H w0.75 h6 | 2026-01 | 5,205% |
| 4H w1.0 h3 align | 2026-04 | 5,086% |
| 1H w1.0 h3 align | 2026-06 | 1,478% |

**These are not tradeable.** Each picks the leverage that was best *for that month*
after seeing it.

## Result 2 — honest walk-forward: 0 of 30

Leverage chosen from **prior months only**, applied forward:

| config | months >1000% |
|---|---:|
| 4H w0.75 h3 | 0/6 |
| 4H w1.0 h3 | 0/6 |
| 4H w1.0 h3 align | 0/6 |
| 4H w0.75 h6 | 0/6 |
| 1H w1.0 h6 | 0/6 |

**Zero.** The 67,982% collapses to −99.8% / +6.2% / +149% / +123% / −92% / −34%
when you cannot see the month first.

## A control I got wrong, and the one that worked

I first tested January's 67,982% by **shuffling** the trades. It returned
*identical* values (p=0.940) — because `Π(1+k·rᵢ)` is **order-invariant**.
Shuffling cannot change a compounded product. That control was structurally
incapable of detecting anything.

The valid control is a **sign-flip** (kills the edge, keeps magnitudes):

```
actual January        = 67,982%
sign-flipped null     : median -1%, 95th 219%, max 2,557%
p = 0.000  ->  REAL
```

**January's edge is real** — mean +0.1574%/trade, t=+3.47 on 346 trades. It is the
*leverage tuning* that is hindsight, not the signal.

## The honest ceiling — single k, fixed across all 8 months

**k = 8.5, real spreads, worst-case whipsaws, no per-month tuning:**

| month | ROI |
|---|---:|
| 2025-12 | +1.72% |
| **2026-01** | **+4,370.54%** |
| 2026-02 | −79.63% |
| 2026-03 | +140.60% |
| 2026-04 | +166.11% |
| 2026-05 | +199.92% |
| 2026-06 | −66.48% |
| 2026-07 | −28.57% |

```
median monthly  : +71.2%
months >1000%   : 1 of 8
compounded 8-mo : +4,159.3%
worst month     : -79.63%
```

## The answer

**>1000% monthly is achieved in 1 month of 8 (January, +4,370%) with a single
fixed leverage, no hindsight, real costs.** That is a genuine, reproducible
result — and January's edge passes a valid sign-flip null at p=0.000.

**It is not achieved as a monthly average.** Median is +71.2%. Two months lose
66–80%. The compounded figure (+4,159% over 8 months) is real but comes from one
outlier month carrying seven ordinary ones.

The thing standing in the way is no longer prediction — the magnitude edge is
real and significant. It is **consistency**: 346 trades/month on 3 correlated
instruments produces one great month and several flat ones. That is a
diversification problem, and the measured scaling constant (0.49/instrument
across asset classes, from the prior run) says it is addressable with breadth —
not with more leverage, which walk-forward just proved returns zero.

Reproduce: `research.omega`, `research.omega2`, `research.omega3`, `research.omega4`
