# REPLACEMENT: STOP PREDICTING. HARVEST.

Every framing in this project — all 40+ tests — assumed returns come from
**prediction**. I never questioned that assumption. It was the actual limiting
factor.

There is a return source that requires **zero directional accuracy**: the
**rebalancing premium** (Shannon's Demon / volatility harvesting).

For a periodically rebalanced portfolio, geometric growth exceeds buy-and-hold by

```
premium = ½ ( Σ wᵢσᵢ²  −  w'Σw )   ≥ 0  always
```

**It contains no μ.** No expected return, no direction. It is a pure function of
**volatility and correlation** — and volatility is the one thing this project
*can* forecast, at IC ≈ 0.50, t=+17. My magnitude edge finally has a
monetisation path that never touches direction.

## Measured on real data

| asset | σ per bar | annualised |
|---|---|---|
| gold | 0.7834% | 30.5% |
| eur | 0.1513% | 5.9% |
| aud | 0.2325% | 9.0% |

correlations: gold/eur **+0.495**, gold/aud **+0.577**, eur/aud **+0.749**

**Theoretical premium: 0.000557%/bar = +0.0724%/month.** That is the entire
prize; everything else is execution cost.

## It works — and it is real

| strategy | final equity | vs B&H | cost paid |
|---|---|---|---|
| buy & hold | 1.00627 | — | 0 |
| rebalance every 6 bars | 1.01203 | +0.00576 | 0.008% |
| **rebalance every 12 bars** | **1.01512** | **+0.00885** | 0.006% |
| rebalance every 30 bars | 1.00973 | +0.00346 | 0.003% |

**Decomposition** (the discipline that killed the last false positive):

```
gross growth      +1.5181%
costs paid        -0.0061%
net               +1.5119%
buy & hold        +0.6268%
REBALANCING ALPHA +0.8851%  =  +0.1137% per month
```

No branch of this code can invent PnL — every bar's contribution is `w'r` with
weights summing to 1. It is a real portfolio by construction.

**Statistically:** per-bar difference t=+1.48, sign-flip p=0.14, halves +1.28
and +0.96. Positive and consistent, **not significant.**

Timing the rebalance with a causal volatility forecast: top-30% dispersion gave
+0.00483 vs +0.00458 for every-bar. Marginal.

---

## The finding that matters — I have been wrong for six turns

I have repeatedly told you the lever is **"more instruments, 0.49 efficiency
each."** The measured scaling law says that is **wrong** for this path:

| N instruments | annual premium |
|---|---|
| 3 | +0.47% |
| 10 | +0.64% |
| 50 | +0.69% |
| **100** | **+0.70%** |

**N saturates almost immediately.** 3 → 100 instruments buys **49% more, not
33× more**, because

```
premium = ½ · σ² · (1 − 1/N) · (1 − ρ)
              ↑              ↑
          QUADRATIC     the real constraint
```

`(1 − 1/N)` is already 0.67 at N=3 and can never exceed 1.0. The binding terms
are **volatility (quadratic)** and **correlation** — not count. My measured
ρ = +0.607 means I am discarding 61% of the available premium by holding three
assets that are all just short-USD.

**What each lever is actually worth:**

| configuration | annual |
|---|---|
| measured now (3 USD pairs, σ 30%, ρ 0.61) | +1.26% |
| 100 instruments, same vol & correlation | +1.87% |
| 3 assets, truly uncorrelated | +3.20% |
| 100 instruments AND uncorrelated | +4.75% |
| 100 uncorrelated at crypto vol (80%) | +32.69% |
| 100 uncorrelated at σ=150% (physically absurd) | +114.91% |

**Leverage cannot bridge the gap**, because the premium is a growth-rate effect:
`g(k) = k·w'μ − ½k²·w'Σw`. Levering past k* *reduces* growth — the optimum is a
maximum, not a monotone. Target growth for 1000%/month is ln(11)×12 = 28.8/yr;
the best harvest ceiling is ln(1.14) = 0.13/yr. **A 221× gap in log-growth.**

## Honest ceiling of the no-prediction path

| | |
|---|---|
| measured here | **+0.11%/month**, t=+1.48 (not significant) |
| theoretical, this universe | +0.47%/year |
| theoretical, ideal universe | ~+14%/year |
| required | +1000%/month |

**The no-prediction path is real, it is free of direction, and it is three
orders of magnitude too small.** Now measured, not asserted.

---

## What this changes

Three things, and two are corrections to my own advice:

1. **A genuinely new return source, requiring no direction at all.** It exists,
   it is positive, and it is the correct home for my volatility edge.
2. **"More instruments" was wrong.** I said it for six turns. The scaling is
   `(1 − 1/N)`, which saturates at N≈10. I was recommending the weakest lever.
3. **The real levers are σ² and (1 − ρ)** — volatility, which is quadratic, and
   decorrelation, where I am currently throwing away 61%.

If I pursue this further, the correct universe is **not more FX pairs**. It is
the **highest-volatility, lowest-correlation** instruments reachable: crypto,
single-name equities, natural gas, VIX futures. Not because more is better, but
because σ² is quadratic and ρ is the binding constraint.

That would plausibly take the harvest from +0.5%/yr to +20–30%/yr. It is real,
it is defensible, and it is still nowhere near 1000%/month — and I would rather
hand you a real +25%/year than a tenth fake +1000%.
