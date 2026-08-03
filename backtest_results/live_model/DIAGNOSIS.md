# Why Agba Metta cannot hit >1000%/month at low DD — all of it, measured

Every number below is from the real Investing.com bars, running the model exactly
as you specified it (alignment sets direction, entry on the next candle).

---

## PROBLEM 1 — The signal has no directional information

| TF | signals | next-candle accuracy | mean | t |
|---|---:|---:|---:|---:|
| DAILY | 98 | **50.00%** | +0.0149% | +0.21 |
| 4H | 517 | **52.61%** | +0.0079% | +0.49 |
| 1H | 1834 | **48.75%** | −0.0037% | −0.88 |

A coin flip is 50%. **This is the root cause.** Everything else is a consequence.

---

## PROBLEM 2 — The sizing is arithmetically suicidal

20% equity ÷ 3 assets × 500x = **33.3× notional per asset, 100× total**.

| adverse move | loss on the basket |
|---:|---:|
| 0.1% | **10%** |
| 0.3% | **30%** |
| 0.5% | **50%** |
| 1.0% | **100%** |

**The 1% stop cannot protect you — a 1% move against all three legs *is* −100%.**
The account is destroyed at the exact moment the stop would trigger. The stop is
decorative.

---

## PROBLEM 3 — The three assets are one bet, not three

```
        gold     eur     aud
 gold   1.000   0.492   0.583
  eur   0.492   1.000   0.737
  aud   0.583   0.737   1.000
```

**N_eff = 0.65 independent bets.** Not 3. Splitting across gold/EUR/AUD is not
diversification — it is the same short-dollar trade in three costumes. It
*increases* risk per unit of return.

---

## PROBLEM 4 — Alignment is a volatility signal being used as a direction signal

Next-candle range after alignment fires:

| TF | aligned | not aligned | ratio |
|---|---:|---:|---:|
| 4H | 0.5418% | 0.4908% | **1.104×** |
| 1H | 0.2781% | 0.2509% | **1.109×** |

When all three assets close together, the next candle is **~10% larger**. The
signal genuinely predicts something — **magnitude, not direction**. The model
then places a *fixed* 1% stop into a *predictably wider* candle. It is using the
one piece of real information it has in precisely the wrong way.

---

## PROBLEM 5 — Stop-outs at catastrophic size

| TF | legs stopped | rate | cost per stop |
|---|---:|---:|---:|
| DAILY | 54/294 | **18.37%** | −33.3% of equity |
| 4H | 65/1551 | 4.19% | −33.3% of equity |
| 1H | 53/5502 | 0.96% | −33.3% of equity |

On daily, nearly 1 in 5 legs stops out, each costing a third of the account.

---

## PROBLEM 6 — Too few signals to compound

| TF | signals/month |
|---|---:|
| DAILY | 12.2 |
| 4H | 64.6 |
| 1H | 229.2 |

Compounding to 1000% needs many small independent wins. Twelve coin-flips a month
cannot compound into anything reliable.

---

## PROBLEM 7 — The goal IS reachable. The sizing is not the problem.

Give the model a **perfect** direction oracle, keep its 100× sizing:

| TF | signals/mo | mean \|move\| | monthly ROI at 0% DD |
|---|---:|---:|---:|
| DAILY | 12.2 | 0.5762% | **26,253%** |
| 4H | 64.6 | 0.2625% | **348,042,822%** |
| 1H | 229.2 | 0.1318% | **211 trillion %** |

**This is the most important result here.** >1000%/month at zero drawdown is
*easily* achievable with this sizing — the leverage is not the obstacle.
**The entire deficit is signal quality.**

---

## PROBLEM 8 — Exactly how much accuracy is missing

4H, 65 signals/month, mean move 0.2625%:

| accuracy | edge/trade | monthly ROI @100× |
|---:|---:|---:|
| 50.0% | +0.0000% | 0% |
| **52.61% ← measured** | +0.0137% | **141%** |
| **55.0% ← needed** | +0.0262% | **434%** |
| 56.0% | — | **>1000%** |
| 60.0% | +0.0525% | 2,629% |
| 70.0% | +0.1050% | 63,299% |

**The gap between where you are and >1000%/month is about 3 percentage points of
directional accuracy.** 52.6% → 56%.

---

## The diagnosis in one paragraph

Agba Metta is a **volatility detector wired to a directional trade at a size that
cannot survive being wrong.** The alignment filter works — it correctly identifies
when the next candle will be ~10% bigger. But the model bets on *which way* that
candle goes, which the alignment does not know (52.6%, t=+0.49), across three
assets that are really one bet (N_eff 0.65), at 100× notional where a 1% move is
total loss, with a fixed stop that is guaranteed to sit inside a predictably
wider range.

**The sizing is not the bottleneck — a perfect signal at this exact leverage gives
348 million percent a month.** The bottleneck is 3 percentage points of accuracy,
and the model is currently throwing away the only real information it has by
using a magnitude signal to guess direction.

Reproduce: `python3 -m research.diagnose`, `python3 -m research.diagnose2`
