# YOUR THREE QUESTIONS — ANSWERED WITH ARITHMETIC

Your question 1 was right and it exposed a real blind spot. I had never
computed it. Here it is.

## Q1 — "If you achieve 80% accuracy, where's leverage?"

**You are completely right. Leverage was never the blocker.**

Kelly with win prob *p*, 1:1 payoff: `f* = 2p−1`, `g = p·ln(1+f) + (1−p)·ln(1−f)`,
130 trades/month:

| accuracy | Kelly f* | monthly ROI |
|---|---|---|
| 52% | 0.04 | 11% |
| 55% | 0.10 | 92% |
| **58.3%** | 0.17 | **~500%** |
| 60% | 0.20 | 1,270% |
| 70% | 0.40 | 4,421,200% |
| **80%** | **0.60** | **7.6 × 10¹²%** |

At 80% accuracy the answer is absurd wealth. I had already proved this myself
with the perfect-oracle test (26,253%/month at 0% drawdown) and **never drew the
conclusion**: the entire game is accuracy. Everything downstream is arithmetic.

## Q2 — "Why have you not achieved >500% monthly?"

**Because I never computed what 500% actually requires.** You pushed, I computed:

> **500%/month needs 58.3% accuracy. Not 80%.**

That reframed everything — the gap looked like a factor of 20 and is actually
**4.9 percentage points** from my best measured 53.4%.

## Q3 — "Did you challenge all the blockers?"

I found one I had never questioned, and you were right that it was unexamined:
**every accuracy figure I ever quoted assumed a 1:1 payoff.** Accuracy and
payoff are *two* levers and I only ever pushed one.

At my **already-measured 53.4%**, a payoff of just **1.22:1** gives 500%/month.
And payoff comes from stop/target geometry, which depends on the **range** —
the one thing I forecast well (IC 0.50, t=+17).

**That was the untested cell.** So I tested it: 24 geometries, walk-forward
direction model + walk-forward range model, true 1H intrabar path resolution,
both-barriers-hit counted as a loss, real spreads.

### The lever works mechanically — and buys nothing

| target | payoff b | win rate |
|---|---|---|
| 0.50× | 0.92 | 49.2% |
| 0.75× | 1.16 | 45.1% |
| 1.00× | 1.23 | 44.2% |
| 1.50× | **1.26** | **43.8%** |

Payoff rose exactly as designed, 0.92 → 1.26. **Accuracy fell by precisely
enough to cancel it.** Best of 24 cells: t=−0.18, Kelly f* = **−0.0071**.
Negative. No leverage helps a negative edge.

### Why — and this is arithmetic, not opinion

For a driftless walk with barriers at −s and +t:

```
P(hit +t first) = s/(s+t)        payoff b = t/s
p·b = [s/(s+t)]·[t/s] = t/(s+t)  and  1−p = t/(s+t)
edge = p·b − (1−p) = EXACTLY ZERO,  for every s and t
```

**Geometry cannot manufacture edge. It can only redistribute it between
win-rate and payoff.** Only *drift* — real directional information — creates
edge. Drift is what I measure at ~zero.

This is the cleanest result in the project, and I only found it because you
insisted the payoff assumption be challenged.

### And it exposed an error in my own reporting

| metric | value |
|---|---|
| direction model, close-vs-open | **53.62%** |
| same model, actually traded with barriers | **43.8–49.2%** |

**Predicting the sign of the close is not the same as winning a barrier trade.**
A bar can close up having first knifed through your stop. My 1H path walk
catches that; the close-vs-open metric hides it completely.

**Every accuracy number I have quoted you was measured the easy way.** The
tradeable number is below 50%. I should have been measuring it on the path from
the start.

---

## The real scoreboard

| | |
|---|---|
| required for 500%/month | **58.3%** |
| my best close-vs-open accuracy | 53.4% |
| **my best barrier-tradeable accuracy** | **49.2%** |
| **true gap** | **9.1 points** |

## What this changes about where to look

The conservation law is genuinely useful, because it eliminates an entire class
of effort. **No amount of trade construction, stop placement, target sizing,
position management, or leverage engineering can create edge.** All of it is
redistribution. That is a large fraction of what retail systems and the V82
spec you sent me spend their complexity on.

Only three things can create edge, and now I know exactly which:

1. **Drift** — genuine directional information. 40+ tests, ~zero.
2. **Convexity** — being long options-like payoffs at below fair value. My
   VRP test says gold vol was *under*priced 8 months, so this is the one
   direction-free candidate left with a real mechanism.
3. **Structural premia** — the rebalancing premium I measured at +0.11%/month,
   real but three orders of magnitude too small.

**Path 2 is the only one I have not exhausted, and it is the correct next
target** — it needs no directional accuracy, and I have already measured the
mispricing that would fund it.

I'd rather give you the equation that proves where the edge *cannot* be than a
tenth fake 1000%. This one narrows the search permanently.
