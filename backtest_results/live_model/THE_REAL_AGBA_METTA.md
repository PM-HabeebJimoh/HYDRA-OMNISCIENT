# The Real Agba Metta Model

Corrected again. I had been adding a step the model does not have.

## Your specification — 11 steps, verbatim

```
 1  Wait for candle close.
 2  Check XAUUSD, EURUSD, AUDUSD direction.
 3  If all 3 close UP from their opens, signal LONG.
 4  If all 3 close DOWN from their opens, signal SHORT.
 5  If mixed, skip.
 6  Enter on next candle open.
 7  Use 20% equity split across the 3 assets.
 8  Use 500x leverage.
 9  LONG stop  = entry x 0.99
10  SHORT stop = entry x 1.01
11  Exit at next candle close unless stop hits first.
```

**Direction comes from the alignment itself.** Steps 3 and 4 *are* the signal.
There is no real-yield step, no regime, no external filter.

## What I kept getting wrong

I have twice described the model as "real yield sets direction → alignment
confirms it." That is the **author's config**, not your model. And it does real
damage:

| | |
|---|---|
| real yield range, whole sample | **1.67 to 2.34** |
| days above 0.7 (CONTRACTION/SHORT) | **409 of 409** |
| days below −0.1 (EXPANSION/LONG) | **0 of 409** |

**The gate is a constant.** It never selects anything. Its only effect is to
delete every LONG signal the alignment produces:

| TF | all-3 aligned | UP (LONG) | DOWN (SHORT) | kept by gate | **DELETED** |
|---|---:|---:|---:|---:|---:|
| DAILY | 98 | 51 | 47 | 47 | **51** |
| 4H | 517 | 269 | 248 | 248 | **269** |
| 1H | 1834 | 907 | 927 | 927 | **907** |

The gate throws away **half the model** — 907 of 1834 signals on 1H — and
contributes nothing in return.

## The model, run as specified

Both sides traded, direction from the alignment, entry on the **next** candle:

**DAILY**

| month | signals | LONG | SHORT | WR | return | *(with gate)* |
|---|---:|---:|---:|---:|---:|---:|
| Dec25 | 4 | 4 | 0 | 66.7% | **+88.78%** | 0 signals |
| Jan26 | 12 | 9 | 3 | 50.0% | **+158.72%** | −42.44% |
| Feb26 | 10 | 6 | 4 | 40.0% | −95.88% | −97.07% |
| Mar26 | 6 | 3 | 3 | 11.1% | −100.00% | −60.17% |
| Apr26 | 19 | 10 | 9 | 35.1% | −99.64% | −90.20% |
| May26 | 19 | 10 | 9 | 49.1% | −94.99% | −87.13% |
| Jun26 | 11 | 4 | 7 | 36.4% | −73.15% | −32.92% |
| Jul26 | 8 | 3 | 5 | 33.3% | −83.52% | −81.78% |

**4H**

| month | signals | LONG | SHORT | WR | return |
|---|---:|---:|---:|---:|---:|
| Dec25 | 50 | 32 | 18 | 50.0% | **+68.11%** |
| Jan26 | 57 | 38 | 19 | 53.2% | **+446.76%** |
| Feb26 | 60 | 36 | 24 | 42.8% | −99.79% |
| Mar26 | 79 | 38 | 41 | 45.1% | −99.98% |
| Apr26 | 84 | 43 | 41 | 48.0% | −96.69% |
| May26 | 67 | 34 | 33 | 59.7% | **+865.99%** |
| Jun26 | 65 | 25 | 40 | 48.2% | −99.99% |
| Jul26 | 55 | 23 | 32 | 48.5% | −50.52% |

**1H** — negative every month (−79% to −99.9%), 180–271 signals per month.

Note Dec25 daily: **4 signals, all LONG**. Under the regime gate that month has
**zero** trades. The gate does not just reduce the model — it can silence it
entirely.

## Summary — the real model

**A candle closes → if XAUUSD, EURUSD and AUDUSD all closed the same way, that is
your signal (all up = LONG, all down = SHORT) → mixed means skip → enter the NEXT
candle's open with 20% of equity split three ways at 500x → 1% stop from entry →
exit that candle's close.**

Five things follow from the real spec:

1. **It trades both directions.** LONG and SHORT, decided by the candles.
2. **No real yield, no regime, no external data.** Price only.
3. **The signal candle is never traded** — you enter the one after it.
4. Best months are **Jan26 4H +446.76%** and **May26 4H +865.99%**.
5. It loses money in most months at 500x on this data. The three timeframes are
   consistent about that.

Reproduce: `python3 -m research.spec_check`, `python3 -m research.true_agba`
