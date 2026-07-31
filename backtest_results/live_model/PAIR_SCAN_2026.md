# All-pairs 2026 scan: are there coins/pairs with >80% alignment accuracy?

**Short answer: 24 combinations show >80% — and every one of them is selection noise.**

Data: 100% real Investing.com, 2026-01-01 -> 2026-07-27, 146 aligned daily bars
across 10 instruments: XAUUSD, XAGUSD, EURUSD, AUDUSD, GBPUSD, NZDUSD, USDCAD,
USDCHF, USDJPY, EURGBP. Plus 1,013 4H and 3,728 1H bars for the core 3.

---

## 1. Straightforward scans — nothing near 80%

**Each pair's own previous-bar direction (best 4):**

| pair | signal | n | accuracy |
|---|---|---:|---:|
| EURGBP | reversal | 135 | 57.0% |
| USDCAD | momentum | 139 | 56.1% |
| AUDUSD | reversal | 141 | 55.3% |
| XAUUSD | momentum | 145 | 53.1% |

**Agba Metta 3-asset alignment predicting each pair (best 4):**

| pair | signal | n | accuracy | 95% CI |
|---|---|---:|---:|---|
| USDCHF | follow | 80 | 62.5% | [51.5, 72.3] |
| GBPUSD | fade | 81 | 61.7% | [50.8, 71.6] |
| USDCAD | follow | 78 | 60.3% | [49.2, 70.4] |
| EURUSD | fade | 80 | 57.5% | [46.6, 67.7] |

**Intraday, core 3** — best 4H = **61.3%** (n=31), best 1H = **54.4%** (n=436).
Nothing approaches 80%.

## 2. Aggressive hunt — 24 combos DO exceed 80%

I searched every 3-pair alignment triplet x every target pair x 4 strength
filters x follow/fade = **4,656 combinations**. Top results:

| accuracy | n | 95% CI | target | dir | triplet |
|---:|---:|---|---|---|---|
| **90.5%** | 21 | [71.1, 97.3] | NZDUSD | fade | XAGUSD+AUDUSD+USDCHF |
| **87.0%** | 23 | [67.9, 95.5] | USDJPY | follow | XAGUSD+NZDUSD+USDCAD |
| **87.0%** | 23 | [67.9, 95.5] | NZDUSD | fade | XAGUSD+AUDUSD+USDCHF |
| **85.7%** | 21 | [65.4, 95.0] | USDJPY | follow | GBPUSD+NZDUSD+USDCAD |
| **83.3%** | 24 | [64.1, 93.3] | NZDUSD | fade | XAGUSD+AUDUSD+USDCAD |

24 combos >=80%. On its face this answers your question. It does not survive.

## 3. Why they are not real

**Test A - the noise benchmark.** I re-ran the identical 4,656-combo search 200
times on sign-randomized days (preserving cross-pair correlation):

    best accuracy from PURE NOISE: median 82.5%, 95th pct 90.5%, max 95.0%
    our best: 90.5%  ->  p = 0.055

Random data *routinely* produces 82.5% winners in this search. Ours is 90.5%.
**Searching 4,656 combos over 146 bars guarantees 80%+ hits even with no edge.**
Note each winner has only n=21-24 trades — one lucky streak.

**Test B - out of sample.** Selected the >=80% combos on Jan-Apr, then traded
them untouched on Apr-Jul:

    mean TRAIN accuracy: 81.0%
    mean TEST  accuracy: 66.1%
    still >=80% OOS: 6/18

Looks encouraging. But running that *entire* select-then-test procedure 200 times
on randomized data:

| | real data | noise (median) | noise (95th) |
|---|---:|---:|---:|
| combos >=80% on train | 20 | 20 | - |
| mean OOS accuracy | 57.5% | 50.1% | 63.1% |
| still >=80% OOS | 3 | 0 | - |

    p = 0.200  ->  INDISTINGUISHABLE FROM SELECTION NOISE

Noise finds exactly as many 80% combos as the real data does.

## 4. What the sample size permits

With n=21, an observed 90.5% has a 95% CI of **[71.1%, 97.3%]** — consistent with
a true rate anywhere from 71% upward, and that is *before* correcting for 4,656
searches. To establish a genuine 80% rate you need roughly **150-200 trades** of
that signal. The most any 80%+ combo here has is **27**.

## Answer to your question

There is **no pair or coin in this 2026 data with a verified >80% alignment
accuracy.** The honest ceiling across every pair, timeframe and signal tested:

- Daily, single clean signals: **~57-62%**
- 4H: **~61%** (n=31) | 1H: **~54%** (n=436)
- The 80-90% combos: **noise**, p=0.055 and p=0.200

The strongest *defensible* candidates are USDCHF-follow (62.5%, n=80) and
GBPUSD-fade (61.7%, n=81) off Agba Metta alignment — both confidence intervals
exclude 50%, though neither survives strict multiple-testing correction.

Per the accuracy table from the previous report, 62% supports roughly
**+5%/month at <5% drawdown** — real, but not 700%.

To test these properly I need more data than 146 bars. 2020-2025 across these
same 10 pairs would give ~1,500 bars and settle it.

Reproduce: `research.scan_pairs`, `research.hunt80`, `research.oos80`,
`research.oosnull`, `research.hunt80_intraday`
