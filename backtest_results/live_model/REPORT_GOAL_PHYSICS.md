# Agba Metta — Can +700%/month at <5% DD be reached? The physics, measured.

All numbers below come from the 100% real Investing.com bars already in this repo
(Dec 2025 – Jul 2026: 3,728 1H bars, 1,013 4H, 202 daily; every file `envelope_fixes=0`).
No synthetic data, no approximations. Reproduce with `python3 -m research.<name>`.

I challenged every assumption in the goal, including the goal itself. Here is what I found.

---

## 1. The first assumption I broke: "more leverage gets us there"

Leverage does not appear in the constraint at all. What matters is
**k = notional / equity**:

    loss on a trade = k x adverse_move

The old model used risk 20% / 3 assets x 500x  ->  **k = 33.3x per leg**.
With a 1% stop that is **-33.3% of equity on ONE leg**, -100% on three.

> **DD < 5% with a 1% stop is arithmetically impossible at that size.**
> It is not a tuning problem. `research/physics.py`

For a 5% max single-trade loss:

| stop | max k allowed |
|---|---:|
| 1.00% | 5.0x |
| 0.50% | 10.0x |
| 0.20% | 25.0x |
| 0.10% | 50.0x |

## 2. What the goal actually demands (`research/requirement.py`)

Leverage scales mean *and* sigma together, so **per-trade Sharpe is leverage-invariant**.
The goal is a Sharpe requirement. Monte-Carlo, requiring P(maxDD<5%) = 95%:

| trades/mo | needed mean/trade | max sigma | per-trade SR | annualised SR |
|---:|---:|---:|---:|---:|
| 10 | +20.79% | 10.27% | 2.03 | **22.2** |
| 40 | +5.20% | 3.34% | 1.56 | **34.1** |
| 200 | +1.04% | 1.26% | 0.82 | **40.3** |

For scale: Renaissance Medallion, the best track record ever recorded, is ~2.5 annualised.
**The goal requires 22–40.** That is 10–16x the best fund in history, sustained.

## 3. The ceiling: compare that to PERFECT FORESIGHT (`research/ceiling2.py`)

Knowing the sign of every future bar in advance, on this real data:

| TF | required per-bar SR | perfect-foresight SR | required as % of perfect | required accuracy |
|---|---:|---:|---:|---:|
| Daily | 1.878 | 0.908 | **207%** | **190%** |
| 4H | 1.078 | 0.875 | **123%** | **132%** |
| 1H | 0.606 | 0.845 | 72% | **97.0%** |

Daily and 4H demand **more than perfect prediction** — mathematically unreachable at any
size, any leverage, any rule. 1H needs **97% directional accuracy on every single bar** for
eight straight months.

## 4. Why the 3 legs cannot diversify the drawdown (`research/corr.py`)

XAU/EUR/AUD open->close correlations are 0.46–0.75. Basket sd is *higher* than the
zero-correlation benchmark: **N_eff = 0.65 independent bets, not 3.** The three legs are one
short-USD bet in a trenchcoat. Splitting 20% across them reduces nothing.

## 5. I searched hard for the edge, and I caught myself faking it

**First attempt reported Daily 72.5%, 4H 75.7%, 1H 75.7% OOS accuracy, t up to +26.9.**
That would have hit the goal. It was a **look-ahead bug**: `np.convolve(x, w, 'same')` is
*centered*, so the moving-average feature contained future bars.

I added a mechanical causality test — perturb bar i's OHLC, assert no feature at row <= i
changes. It flagged `bma5` and `bma20`. After the fix (`research/predict2.py`):

| TF | leaked | leak-free |
|---|---:|---:|
| Daily | 72.50% | **55.05%** (t +0.98) |
| 4H | 75.74% | **53.02%** (t +0.59) |
| 1H | 75.70% | **48.40%** (t -1.18) |

The entire "edge" was the bug. This is exactly the class of error that produced the old
+70,174,712% March figure.

Then a wide leak-free search — 30+ causal features x ridge/logistic x 4 regularisations x 3
timeframes (`research/search.py`) — best honest OOS accuracy **56%**, t-stats
indistinguishable from their own shuffled-label controls.

## 6. Exhaustive search of YOUR rule family (`research/gridsearch.py`)

2,016 configs: follow/fade x holding 1-5 bars x 4 stops x 3 strength filters x 7 asset
subsets x 3 timeframes. Best |t| = 5.49 — but it is a **losing** fade (mean -0.13%/trade);
its mirror image does not profit, because the stop asymmetry eats it.

Only one candidate was positive, persistent across both chronological halves, and positive
in 7 of 8 months: **4H gold momentum**, hold 5 bars, 1% stop, 0.3% min strength.
n=527, +0.2263%/trade, t=+3.37.

## 7. I sized that one honestly (`research/best.py`) — with real costs

XAUUSD round-trip 0.7bp of notional (ECN typical):

| k | monthly | maxDD |
|---:|---:|---:|
| 1x | +14.6% | -16.7% |
| 5x | +71.7% | -64.6% |
| 10x | +116.1% | -91.6% |
| 30x | -53.6% | **-100%** |

Note k=30x *loses* — past the growth-optimal point, more size lowers return and guarantees
ruin. **The largest size respecting DD<5% is k=0.28x -> +4.06%/month.**

**+4.06% vs the +700% target: a 172x shortfall.**

## 8. And even that survivor does not survive (`research/deflate.py`)

Re-ran the entire grid 200 times on bar-sign-randomized data (preserving cross-asset
correlation) to get the empirical distribution of the best-of-2,016 |t|:

    null max|t|: median 2.75, 95th pct 3.55, max 4.66
    p-value of the best config after selection = 0.375

**t=+3.37 sits below the 95th percentile of pure noise.** The 4H gold edge is
selection noise. There is no verified edge left.

---

## Conclusion

+700%/month at <5% DD is not blocked by laziness or by insufficient tuning. It is blocked in
this order, and the first two are absolute:

1. **Daily and 4H require better-than-perfect foresight** — >100% of the omniscient ceiling.
2. **1H requires 97% accuracy on every bar for 8 months.** Measured honest accuracy: ~50%.
3. The three legs are 0.65 independent bets, so the DD cannot be diversified away.
4. The only candidate that passed persistence testing dies to multiple-testing correction.

The old numbers that appeared to reach the goal were produced by the two mechanisms I
isolated here: a **look-ahead bug** and a **basket loss cap** that books -2% while the real
adverse move was -31% (the Dec 23 4H trade in the prior report). Both make the equity curve
print returns the market never paid.

## What is actually reachable on this data

- k=0.28x, 4H gold momentum: **+4.06%/mo at -4.86% DD** — and I do not trust even this,
  per section 8.
- Raising it requires **new uncorrelated return streams** (more instruments, genuinely
  different signals), because Sharpe scales with sqrt(N_eff) and N_eff is currently 0.65.
  That is the only lever the physics leaves open — not leverage, not caps, not sizing.

I can pursue that next: widen to the majors already in `data/raw/majors/` and `xpairs/` and
measure N_eff and Sharpe honestly. I will not present a number I have not tried to break.
