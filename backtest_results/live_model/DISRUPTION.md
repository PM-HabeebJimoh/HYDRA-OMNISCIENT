# REPLACEMENT MINDSET — FOUR NEW FRAMES, AND THE NINTH FALSE POSITIVE

You were right that I had been asking **one question in one frame**: *"will
XAUUSD rise in USD terms next bar?"* That question is unpredictable (0/34), and
I had been treating it as if it were the only question. It isn't. Four
replacements, none previously tested.

## R1 — CROSS-SECTIONAL instead of time-series

All three assets are quoted vs USD, so they share one enormous common factor:
**the dollar**. That factor is what's unpredictable. A dollar-neutral long/short
kills it by construction and asks only about the residual.

| pair | accuracy | z | traded spread |
|---|---|---|---|
| gold/eur | 51.62% | +0.92 | t = −0.85 |
| gold/aud | 50.25% | +0.14 | t = −1.95 |
| eur/aud | 53.12% | +1.77 | **t = −3.63** |

Removing the dollar does not reveal a predictable residual. Costs (0.024–0.039%
round trip on two legs) exceed any signal. **Fails.**

## R3 — PATH ORDER instead of endpoint

"Which barrier is touched *first*" is a different random variable from "where
does it close." Barrier order carries information that close−open destroys.

gold 50.92% (z=+0.38) · eur 48.62% (z=−0.57) · aud 48.42% (z=−0.66). **Fails.**

## R4 — ASYMMETRY instead of mean

If I can't predict the mean but *can* predict skew, a convex payoff profits at
50% directional accuracy.

gold skew-sign **54.86%, z=+2.75** — the only direction-adjacent result to clear
2 in this entire project. But traded: t=+1.65, and eur/aud are t=−3.58/−4.54.
One cell of three, failing on the money leg. **Fails.**

## R2 — INVERT THE MAGNITUDE TRADE

This one looked like the answer.

My magnitude model is 74–79% accurate but **loses money bought as a straddle**,
because bracket width scales with the forecast so signal and hurdle cancel.
That cancellation is a property of **buying** range. Sell range on
predicted-quiet bars and the same scaling should work *for* me. I'd run the buy
side ~20 times and never once run the mirror.

**Initial result:**

| | WR | mean | t |
|---|---|---|---|
| gold | 84.0% | +0.1383% | +5.76 |
| eur | 83.5% | +0.0394% | **+9.78** |
| aud | 83.5% | +0.0603% | +9.46 |

| leverage | WR | median month | maxDD |
|---|---|---|---|
| 1× | 83.7% | +10.58% | 6.17% |
| **4×** | **83.7%** | **+48.94%** | **22.96%** |
| 8× | 83.7% | +119.39% | 41.66% |

**WR 83.7% — your >80% bar, cleared.** And it passed seven audits:

- **Loss tail** — win/loss ratio 0.38–0.57, but wins outnumber losses enough
- **Pessimistic stops** — still t=+2.50 to +6.05
- **Both vol regimes** — low VIX t=+2.97, high VIX t=+5.22 (*stronger* in stress)
- **Split-half** — gold +3.66/+5.59, eur +7.15/+6.78, aud +6.89/+6.87
- **Monthly** — 20 of 21 months positive
- **Sign-flip null** — p = 0.0000 on all three
- **True 1H intrabar path** (not just OHLC) — edge got *bigger*, ratio 1.23–1.45

Everything said real.

---

## It was a bug in my own code

The one test that isn't a robustness test — **decomposition: which branch of my
own code paid me, and is that branch a real trade?**

```
GOLD  total +110.95%
    NEVER TRADED   n=601  contributes +187.48%   (169% of total)
    one stop       n= 42  contributes  -91.37%
    faded down     n= 83  contributes  +17.15%
    faded up       n= 76  contributes   -2.32%
```

The final branch of `fade()` read:

```python
return abs(c-o)/o - hs      # "never reached the band"
```

If price never touches either side of the band, **no trade was ever opened.**
Correct PnL is 0. I booked `abs(c-o)/o` — a *guaranteed positive* number, the
absolute size of the bar's move — as profit, on **601 of 802 bars (74.9%)**.

That is exactly where the 83.7% win rate came from: three-quarters of all bars
were free fake wins.

**Corrected:**

| | before | after |
|---|---|---|
| WR | 83.7% | **11.1%** |
| gold | +110.95% | **−76.54%** |
| eur | +31.59% | **−7.79%** |
| aud | +48.39% | **−13.16%** |
| median month @4× | +48.94% | **−14.33%** |
| maxDD @4× | 22.96% | **74.01%** |

**Ninth false positive, found and killed.**

## The lesson worth more than the result

**Seven robustness audits could not find this.** Split-half, sign-flip null,
regime splits, stop sensitivity, pessimistic fills, monthly consistency,
intrabar path — a constant positive bonus applied to 75% of bars is robust to
every one of them. It splits evenly. It survives sign-flip (magnitudes are real,
only signs permute). It appears in both vol regimes. It makes every month
positive.

**Robustness testing cannot detect a specification error.** Only decomposition
can. From now on the first question about any winning result is not "does it
survive the null" but **"which line of my code produced the money, and is that
line a trade someone could actually place?"**

## Where this leaves the answer

Four genuinely new frames — cross-sectional, path-order, skew, inverted
magnitude. All four fail. That is now **38 direction tests across 9 data layers
and 5 problem framings**, zero survivors.

And I want to be exact about what I have and haven't shown. I have not proven
direction is impossible — I've shown that **every angle reachable from this
sandbox with free data has failed**, and I've measured *why*: at the one moment
direction was demonstrably real (the release instant, t=+2.37), **87.6% of it
was gone within 5 minutes** and the remainder was smaller than the spread.

**Defensible result, unchanged:**
- **Magnitude: 74–79% confident accuracy, IC ≈ 0.50, t = +15 to +17** — real,
  walk-forward, from combining all nine layers
- **Direction: ~50%**
- **Money: +8.1%/month at 21.6% DD, or +0.14%/month at 2.8% DD calendar-gated**

Nine times in this project a result has said ">1000%" or ">80%". Nine times it
was my own error. The tenth might be real — but the discipline that finds the
error is the only thing that would let either of us tell the difference.
