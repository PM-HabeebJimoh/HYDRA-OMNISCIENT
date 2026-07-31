# Did we achieve +700%/month at <5% DD?

# NO.

Best honest result, on 100% real Investing.com data, with real costs:

| attempt | monthly ROI at DD<5% | vs 700% goal |
|---|---:|---:|
| Original model (V1 500x) | wiped to -100% | fail |
| V3 (7 enhancements, 400x, -2% cap) | best month +374%, DD -11% to -19% | fails DD |
| 4H gold momentum (best of 2,016 configs) | **+4.06%** | 172x short |
| 10-instrument portfolio (widest set) | **+1.24%** | 565x short |

## Why. One table.

Max monthly ROI achievable while keeping maxDD<5%, as a function of how often
you correctly call direction (real 4H bar magnitudes, real costs):

| accuracy | monthly ROI at DD<5% |
|---:|---:|
| 50% | +0.0% |
| 55% | +1.4% |
| 60% | +4.6% |
| 70% | +16.8% |
| 80% | +30.2% |
| 90% | +62.5% |
| 95% | +96.4% |
| 98% | +186.0% |
| **100%** | effectively unbounded |

**Our honest, leak-free measured accuracy is ~55%.** That buys +1.4%/month.

**+700%/month requires ~100% accuracy — being right on essentially every single
trade for eight months straight.** At 98% accuracy, the best in existence by an
enormous margin, you still only reach +186%.

That is the whole answer. The gap is not leverage, sizing, caps, or tuning.
Those were all tested and none of them move this table, because leverage
multiplies wins and losses equally.

## The two things that made old results LOOK like they hit the goal

1. **A look-ahead bug.** A centered moving average (`np.convolve(...,'same')`)
   leaked future bars. It printed 72-76% accuracy. Fixed -> 48-55%.
2. **The -2% basket cap.** On the Dec 23 4H trade the real adverse move was
   **-31.41%** of equity; the cap booked **-2.00%**. The curve records money the
   market never paid. Remove it and the same curves go to -100%.

Both were removed. What remains is the table above.

## What IS real and achievable here

+1.2% to +4.1% per month at <5% drawdown — and I do not fully trust even that:
the 4H gold edge (t=+3.37) sits *below* the 95th percentile of best-of-2,016
selection noise (3.55, p=0.375).

Reproduce: `python3 -m research.answer`, `research.wideport`, `research.deflate`
