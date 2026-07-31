# AGBA METTA V82 — July 2026

Same engine as the 8-month run. Warm-up (MA/ATR/streak) taken from bars **before**
July so indicators are fully formed; only trades **entered in July** are counted.

Universe XAUUSD/EURUSD/AUDUSD · forecast 4H / execute 1H · risk 0.1%/trade ·
12-bar time exit · real spreads applied.

## Coverage — read this before the numbers

    13 of 23 July weekdays have full 3-asset 1H data.
    ABSENT: 07-03, 07-09, 07-15, 07-21, 07-22, 07-27, 07-28, 07-29, 07-30, 07-31
    Binding limit: AUDUSD 14/23 days. EURUSD 16/23. XAUUSD 20/23.
    => July is 57% covered.

The engine also trades partial days (07-03, 07-05, 07-21, 07-22 appear in the log
with fewer than 20 aligned bars). Those are real bars, but the month is not whole.

## Results

| variant | n | WR | meanR | t | ROI | maxDD |
|---|---:|---:|---:|---:|---:|---:|
| V82 as-specified (1.0/2.0, trend filter) | 255 | 29.41% | −0.1472 | −1.79 | **−3.70%** | 7.12% |
| AGBA V82 (0.5/3.0, no trend filter) | 773 | 17.21% | −0.0594 | −0.72 | **−4.68%** | 13.20% |
| **AGBA V82 + alignment confluence** | **321** | **22.43%** | **+0.2019** | **+1.44** | **+6.59%** | **6.95%** |

**July is the weakest month of the eight.** In the full run it was the only
negative month for the no-alignment variant (−4.68%). The alignment variant turns
it positive at **+6.59%**, but t = +1.44 — **not statistically significant on one
month**.

## Detail — alignment variant

    exits: stop=244 (76.0%)   target=42 (13.1%)   time=35 (10.9%)
    trades by asset: gold 119, eur 109, aud 93

**76% of trades stopped out.** With a 0.5×ATR stop and 3.0×ATR target that is by
design — the geometry needs roughly 1 win per 6 to break even. In July it barely
cleared that.

Equity path ($10,000 start, 0.1% risk):

| day | P&L | equity |
|---|---:|---:|
| 07-01 | +28.49 | $10,028.49 |
| 07-06 | −141.42 | $9,747.57 |
| 07-08 | −199.61 | $9,524.70 |
| 07-13 | −131.83 | $9,412.12 |
| **07-14** | **+583.42** | $9,995.54 |
| 07-17 | −52.55 | $10,002.30 |
| **07-23** | **+612.22** | $10,599.78 |
| 07-24 | +58.88 | **$10,658.66** |

The account was **down 5.9% by 07-13**, then two days — 07-14 and 07-23 — produced
+$1,195 of the +$658 net. **Remove either one and July is negative.** That is the
honest shape of this month: a long grind of small stop-outs rescued by two
outliers.

## Move-size gate

| bucket | n | meanR | t |
|---|---:|---:|---:|
| smaller half ATR | 161 | +0.0874 | +0.47 |
| **larger half ATR** | **161** | **+0.3086** | **+1.50** |

Correct direction — edge concentrated in larger bars, not the quiet ones. Same
signature as the 8-month run, so July is consistent with a real effect even though
it is weak.

## Risk scaling

| risk | ROI | maxDD |
|---:|---:|---:|
| **0.10%** | **+6.59%** | **6.95%** |
| 0.25% | +16.85% | 16.59% |
| 0.50% | +34.86% | 30.69% |
| 1.00% | +73.30% | 52.67% |

## Verdict

**July 2026: +6.59% at 6.95% max drawdown**, 321 trades, net of spreads.

Set against your >1000% target: **July alone does not reach it, and I won't
manufacture it by raising risk.** The 1.00% row shows +73.30% — with a 52.67%
drawdown, which is not survivable.

Two things this run establishes:
1. The alignment filter is doing real work. Without it July is −4.68%; with it,
   +6.59%. That is your original idea earning its place.
2. **One month is not a sample.** t = +1.44. The 8-month figure (+988.89%,
   t = +14.54) is the meaningful number; July shows the month-to-month variance
   inside it.

The missing 10 weekdays matter — 07-27 to 07-31 alone is a full week absent, and
AUDUSD is the constraint. Completing July needs AUDUSD 1H for those days.

Reproduce: `python3 -m research.agba_v82_july`
