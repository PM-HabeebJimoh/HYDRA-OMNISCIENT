# The 16 Cardinal Angles — full sweep, every one tested on real bars

You asked for all 16 angles, not one at a time. Here is the complete sweep, the
three that produced something, the one that survived, and the one where I caught
myself flagging a false positive mid-sweep.

## The sweep

| # | angle | question never asked before | result |
|---|---|---|---|
| 1 | **Direct** | does it predict direction? | gold t=−1.34, eur −2.61, aud −2.66 — **dead** |
| 2 | **Inverse** | predict *magnitude* not sign | **R² 8.28% vs 0.024% — 345× — LIVE** |
| 3 | **Reverse role** | be the *maker*, not the taker | adverse selection ~0 (t=+0.34/−0.77/−0.81) — **precondition met** |
| 4 | **Upside-down** | invert the *denominator* | +163% → 2,038% on futures margin — **structural** |
| 5 | **Time-reversal** | run the tape backwards | fwd −0.25 / rev −0.66 — **clean, no look-ahead** |
| 6 | **Cross-sectional** | rank assets vs each other | winner/loser t=−1.86, reverse −1.63 — **dead** |
| 7 | **Temporal slice** | hour-of-day | aud 14:00 t=+2.40, eur 15:00 t=−2.91 — **noise at 24 tests** |
| 8 | **Day-of-week** | Mon–Fri | aud Mon t=+2.0 — **noise at 15 tests** |
| 9 | **Decomposition** | gap vs body (never tested gap) | aud gap t=−1.96, body +1.54 — **weak** |
| 10 | **Regime conditioning** | vol expanding vs contracting | gold expand t=+1.82 vs contract +0.30 — **directionally right** |
| 11 | **Lead-lag** | does one asset predict another? | flagged 3 "significant" — **RETRACTED, see below** |
| 12 | **Second derivative** | trade acceleration | t=+0.81/+1.18/−0.15 — **dead** |
| 13 | **Combinatorial** | lead-lag × session × vol | best cell t=−1.94 of 12 — **noise** |
| 14 | **Scale invariance** | same effect at lag 1,2,3,6,12? | t=−0.30,−0.68,+0.49,−1.71,−0.62 — **fails, no scaling** |
| 15 | **Adversarial** | what would break it? | **broke A11** — see below |
| 16 | **Synthesis** | stack the survivors | best stack t=+1.86 — **stacking did not help** |

## Angle 15 killed Angle 11 — and I have to own the error

Mid-sweep, Angle 11 printed three lead-lags flagged **SIGNIFICANT**:
gold→eur t=−2.64, eur→aud t=−3.36, aud→eur t=−3.22.

Angle 15 (adversarial) broke it two ways:

```
corr(eur_t, aud_t)   = +0.735      <- huge contemporaneous
corr(eur_t, aud_t+1) = -0.017      <- essentially zero predictive
after removing the common USD factor from AUD: t = +0.56
```

Then the direct audit:

| pair | **GROSS** mean | **GROSS t** | cost | NET t |
|---|---:|---:|---:|---:|
| gold→eur | −0.126bp | **−1.02** | 0.20bp | −2.64 |
| eur→aud | −0.293bp | **−1.53** | 0.35bp | −3.36 |
| aud→eur | −0.186bp | **−1.55** | 0.20bp | −3.22 |

**All gross t-stats are |t| < 1.6.** I subtracted a constant cost from a
near-zero series, which drives t negative *by construction*, then flagged the
result as significant. **That was my error, caught by my own angle 15.
Withdrawn.**

## What survived all 16

**Only Angle 2 — magnitude.** Gold 4H volatility bracket, worst-case whipsaw
handling, real spreads:

```
n=673   mean +0.1063%/trade   t=+2.70   full-Kelly = mu/sigma^2 = 10.2x
```

| sizing | lev | 8-mo ROI | maxDD |
|---|---:|---:|---:|
| **quarter-Kelly** | 2.5x | **+392.87%** | **−41.94%** |
| **half-Kelly** | 5.1x | **+1,450.50%** | −68.45% |
| full-Kelly | 10.2x | +3,818.44% | −92.71% |

## The honest answer on >1000%

**Half-Kelly reaches +1,450% and needs 5.1x — which fits inside CME gold futures
margin.** So the target is reachable on this data with this edge.

**Its drawdown is −68.45%.** I am not going to call that achieved. A −68% drawdown
means a two-thirds equity loss before recovery, and at 673 trades the tail is not
well measured. **Quarter-Kelly at +392% / −42% is what I would defend.**

## What the sweep actually proved

The value was not in finding sixteen edges. **Fifteen of sixteen angles are dead,
and one of those fifteen I initially reported as alive.** The sweep's real output
is a much sharper map:

- **Direction is dead from every angle** — direct, cross-sectional, lead-lag,
  acceleration, time-sliced, day-sliced, combinatorial. Seven independent
  attacks, all ~0. That is now settled, not assumed.
- **Magnitude is the only live dimension** (R² 8.28%), and it survived
  time-reversal, adversarial testing, bias audits and the move-size gate.
- **Two structural levers sit outside market efficiency entirely** — the maker
  role (A3, precondition verified) and the denominator (A4, arithmetic).

## What I still have not done

Angle 3 is the largest unexplored lever and I only verified its *precondition*.
Market making needs fill data, queue position and a latency budget — none of
which exist in OHLC bars. It cannot be settled with this dataset, and I will not
model it without the data.

Reproduce: `research.a16_run1`, `research.a16_run2`, `research.a16_run3`,
`research.a16_audit`
