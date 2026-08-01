# Task 1 and Task 2 — results

## TASK 1 — find the 3 points of accuracy

Baseline 4H directional accuracy: **52.61%**. Target: **~56%**.

I built 11 causal filters (using only the closed signal candle and earlier) and
tested them on all three timeframes — **33 tests**.

**Best candidate: 4H "close mid-candle" (indecision) filter**

| | |
|---|---|
| full sample | **56.98%** (n=258, t=+2.24) — **+4.37pp** |
| first half | 53.49% (t=+1.22) |
| second half | 60.47% (t=+2.41) |

Month by month: 53.9 / **69.7** / 43.8 / 51.2 / **64.7** / 52.8 / **61.3** / 60.0 %

It clears the +3pp target and holds in both halves. Then I ran the null.

**Empirical null — repeat the entire 33-test search on sign-flipped data:**

```
actual best gain = +4.37pp
null: median +5.10pp,  95th +11.50pp,  max +17.53pp
p = 0.603  ->  SELECTION NOISE
```

**Searching 33 filters produces a +5.10pp winner by chance alone.** My +4.37pp is
*below* the noise median. Task 1 **fails**.

Every other candidate was worse or smaller: DAILY "close near extreme" showed
+22pp but on n=25 (t=+1.51 — meaningless), and DAILY/1H baselines are 50.00% and
48.75%, i.e. nothing to build on.

**Verdict: the 3 points of accuracy are not in this data.** Direction is dead
from 33 angles now, on top of the 7 attacks from the earlier sweep.

---

## TASK 2 — bet magnitude instead

The signal's real content: after alignment, the next candle's range is **1.104×
larger (4H)**. So trade a **bracket** — buy-stop above, sell-stop below, whichever
fires you ride. You never need the direction.

Honest handling: if both triggers hit inside one candle, OHLC cannot say which
came first → booked as the **worst case** (whipsawed both ways, full double loss).
Real spreads on both legs.

**4H, width 1.0×ATR, hold 3 bars:**

```
n=1978   WR 49.34%   mean +0.0394%/trade   t=+2.76
```

| test | result |
|---|---|
| split-half | first +1.62, second **+2.56** — strengthens |
| **move-size gate** | smaller half +0.0063% (t=+0.89), **larger half +0.0726% (t=+2.62)** |
| **sign-flip null** | actual +2.76 vs null median +0.12, 95th +1.76 → **p=0.0020 REAL** |

The move-size gate is the important one: the edge **grows with move size**, which
is the signature of genuine volatility capture. A bid-ask-bounce artifact does
the opposite — that test is what killed my EURUSD result earlier.

**Month by month:** Dec −0.02, **Jan +0.16 (t=+3.32)**, Feb −0.08, Mar +0.05,
**Apr +0.09 (t=+2.94)**, **May +0.05 (t=+2.03)**, Jun +0.01, Jul +0.00.
Six of eight positive.

**What it pays (full-Kelly = 9.8×, worst single trade −4.21%):**

| sizing | leverage | median monthly | worst month | 8-month |
|---|---:|---:|---:|---:|
| quarter-Kelly | 2.4× | **+18.2%** | −36.3% | +429.8% |
| half-Kelly | 4.9× | **+28.9%** | −62.1% | +1,665.3% |
| full-Kelly | 9.8× | +24.4% | −89.5% | +4,795.1% |

---

## The finding you should care about most

**The Agba Metta alignment gate adds nothing to the magnitude bet:**

```
WITH alignment gate : n=1004  mean +0.0429%  t=+2.15
WITHOUT gate (all bars): n=1978  mean +0.0394%  t=+2.76
```

Gating on alignment **halves the sample and lowers the t-stat**. The volatility
edge is present on *every* 4H bar, not just aligned ones. The alignment filter is
not selecting anything useful — it is just throwing away half your trades.

---

## Bottom line on both tasks

- **Task 1 failed.** 33 filters, best gain +4.37pp, but noise produces +5.10pp
  median in the same search. p=0.603.
- **Task 2 succeeded, and it is the first thing in this project to pass every
  gate**: split-half, move-size, and a sign-flip null at p=0.0020.
- It pays **+18% to +29% median monthly**, not >1000%. To get 1000% you need
  ~4.9× leverage *and* a −62% worst month, which is the same ruin trade as before.
- And it works **better without the alignment filter at all**.

Reproduce: `research.task1`, `research.task1b`, `research.task2`, `research.task2b`
