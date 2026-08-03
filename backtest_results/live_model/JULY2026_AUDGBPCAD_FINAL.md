# AGBA METTA MODEL — AUDUSD + GBPUSD + USDCAD — July 2026 — Daily / 4H / 1H

## First: a second error in my own audit

My retraction claimed epoch `1783641600` was 07-17. **It is 07-10.** I computed
the July weekday→epoch map properly this time before fetching anything:

    07-09 = 1783555200    07-10 = 1783641600    07-17 = 1784246400    07-23 = 1784764800

The days I had actually missed were **07-09, 07-10, 07-17, 07-23** — not the set
I named. I fetched all four for both pairs.

## Coverage — asserted against the calendar, not self-reported

| pair | 1H bars | full days | envelope_fixes |
|---|---:|---:|---:|
| GBPUSD | 399 | 17 | **0** |
| USDCAD | 399 | 17 | **0** |

Verified against independently fetched daily OHLC: GBPUSD **17/17 days inside the
daily envelope**, USDCAD **16/17** (07-20 1H high 1.40870 vs daily 1.40740, a
1.3-pip session-boundary difference).

**But the basket is limited by AUDUSD, not by the pairs I fetched:**

```
July 2026 weekdays                     : 23
Days with >=20 aligned 3-asset 1H bars : 13
Present : 07-01,02,06,07,08,10,13,14,15,16,17,20,23
ABSENT  : 07-03,09,21,22,24,27,28,29,30,31
1H COVERAGE = 13/23 = 57%   <-- NOT a full month
DAILY coverage = 21/23 = 91%
```

GBPUSD/USDCAD are now complete for 17 days, but **AUDUSD's 1H feed only has 14
full July days**, and the 3-asset intersection is 13. I cannot fix that by
fetching more GBP/CAD. **The 1H and 4H results below still rest on 57% of the
month.**

## Results

Risk 20% | Leverage 500x | Hard stop 1% | Capital $100,000

| TF | timing | signals | days | bar_WR | asset_WR | stops | return | maxDD | final |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DAILY | SIGNAL-BAR | 4 | 4 | 100.0% | 100.0% | 0 | **+131.81%** | 0.00% | $231,809 |
| DAILY | **LIVE** | 4 | 4 | 0.0% | 25.0% | 1 | **−46.73%** | −46.73% | $53,267 |
| 4H | SIGNAL-BAR | 7 | 5 | 100.0% | 100.0% | 0 | **+81.44%** | 0.00% | $181,436 |
| 4H | **LIVE** | 7 | 5 | 57.1% | 47.6% | 0 | **−0.01%** | −7.02% | $99,995 |
| 1H | SIGNAL-BAR | 17 | 11 | 100.0% | 100.0% | 0 | **+112.86%** | 0.00% | $212,860 |
| 1H | **LIVE** | 17 | 12 | 64.7% | 47.1% | 0 | **+20.44%** | −10.16% | $120,442 |

## What changed from the retracted run

| TF | retracted (13 days, wrong days) | now (correct days) |
|---|---:|---:|
| 4H | −8.18% | **−0.01%** |
| 1H | −9.81% | **+20.44%** |

Both moved materially. That is the point of the retraction: those numbers were
computed on the wrong subset of days and were not reportable. The daily result
(−46.73%) is unchanged, because daily never depended on the 1H transcription.

## What holds

**The timing effect reproduces on every timeframe, again.** Every SIGNAL-BAR row
shows 100% bar win rate, 100% asset win rate, 0 stops, 0.00% drawdown — the
signature of entering a bar whose close was already used to generate the signal.
Moving entry to the next bar's open turns +131.81% / +81.44% / +112.86% into
−46.73% / −0.01% / +20.44%.

**Daily is the worst timeframe, and one trade explains it.** AUDUSD 07-13 → 07-14
entered 0.69180 and stopped at 0.69872, −1.000%, **−$32,467** on a $100k account.
That single stop-out is essentially the whole −46.73%. On 4H and 1H **no stop was
hit at all** across 21 and 51 asset trades.

## What I will not claim

- **1H +20.44% is not a validated result.** 17 signals over 13 of 23 weekdays.
  It is one number from a partial month, and it flipped sign when the day set was
  corrected. I am reporting it, not endorsing it.
- I am not repeating "intraday beats daily." The direction is consistent across
  both runs, but 4H is −0.01% — indistinguishable from zero — and the sample is
  far too small to rank timeframes.

## To actually complete July 1H

AUDUSD needs 07-03, 07-09, 07-21, 07-22, 07-24, 07-27..07-31 — 10 weekdays, and
its feed may genuinely stop at 07-27 as previously documented. GBPUSD/USDCAD need
07-24, 07-27..07-31. Until AUDUSD is complete, 1H/4H for this basket cannot cover
the month, regardless of how much GBP/CAD data I fetch.

Data: `data/raw/intraday_x/{GBPUSD,USDCAD}_2026jul_1h.json` (399 bars each, 0 fixes)
Trades: `backtest_results/live_model/july2026_audgbpcad_final.json`
Reproduce: `python3 -m research.july_final_audgbpcad`
