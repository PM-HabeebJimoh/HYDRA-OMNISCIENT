# Per-currency Agba-Metta signal study, 2025 -> 2026

Timing is the Agba-Metta rule throughout: **signal is read on a CLOSED bar, entry
is the NEXT bar's open, exit that bar's close.** No same-bar entry, no look-ahead.
Each currency examined individually, not as a combination search.

## Data inventory (checked before use)

| pair | bars | range | 2025 | 2026 | flat bars | weekend bars |
|---|---:|---|---:|---:|---:|---:|
| XAUUSD | 409 | 2025-01-02 -> 2026-07-29 | 259 | 150 | 1 | 0 |
| EURUSD | 409 | 2025-01-02 -> 2026-07-29 | 259 | 150 | 6 | 0 |
| AUDUSD | 409 | 2025-01-02 -> 2026-07-29 | 259 | 150 | 4 | 0 |
| XAGUSD | 149 | 2026-01-01 -> 2026-07-28 | 0 | 149 | 1 | 0 |
| GBPUSD | 149 | 2026 only | 0 | 149 | 1 | 0 |
| NZDUSD | 149 | 2026 only | 0 | 149 | 2 | 0 |
| USDCAD | 149 | 2026 only | 0 | 149 | 3 | 0 |
| USDCHF | 149 | 2026 only | 0 | 149 | 2 | 0 |
| USDJPY | 149 | 2026 only | 0 | 149 | 2 | 0 |
| EURGBP | 149 | 2026 only | 0 | 149 | 5 | 0 |

**Important:** only XAU/EUR/AUD have 2025. `data/raw/majors/` contains 2025 and 2023
filenames but **every one of those files is empty (0 bars)** — they were never
populated. The other 7 pairs are 2026-only. I did not fabricate the missing 2025.

## Results — significant findings only

Signals tested per currency: own prior-bar follow/fade, the same with 0.3%/0.6%
strength gates, core-3 alignment follow/fade, and alignment with a strength gate.
`*` = 95% confidence interval excludes 50%.

| pair | best signal | n | accuracy | 95% CI |
|---|---|---:|---:|---|
| **XAUUSD** | **AM-align FADE** | 214 | **57.94%** * | [51.2, 64.4] |
| XAUUSD | own prior-bar FADE | 406 | 54.93% * | [50.1, 59.7] |
| **USDCHF** | AM-align FOLLOW, str>=0.3% | 75 | **61.33%** * | [50.0, 71.5] |
| **GBPUSD** | AM-align FADE, str>=0.3% | 75 | **61.33%** * | [50.0, 71.5] |
| XAGUSD | AM-align FADE | 82 | 59.76% | [48.9, 69.7] |
| USDJPY | AM-align FOLLOW, str>=0.3% | 73 | 58.90% | [47.4, 69.5] |
| NZDUSD | AM-align FADE | 82 | 57.32% | [46.5, 67.5] |
| USDCAD | own prior-bar FOLLOW | 142 | 56.34% | [48.1, 64.2] |
| EURGBP | own prior-bar FADE | 138 | 55.80% | [47.5, 63.8] |
| AUDUSD | AM-align FADE | 211 | 53.08% | [46.4, 59.7] |
| EURUSD | AM-align FADE | 213 | 51.17% | [44.5, 57.8] |

**Nothing reaches 80%.** Best across every currency and signal: **61.3%**.

Note the consistent pattern: alignment **FADES** on the commodity/risk currencies
(XAU, XAG, NZD, GBP, AUD) and **FOLLOWS** on the USD-quoted pairs (USDCHF, USDJPY,
USDCAD). That is one dollar-reversal effect seen from both sides, not 10 signals.

## The one candidate with real history: XAUUSD AM-align FADE

The only finding with 2025+2026 behind it. Stability:

    2025: 58.33% (n=132)     H1: 58.77%      2025Q1 53.8%  2025Q2 75.0%
    2026: 57.32% (n= 82)     H2: 57.00%      2025Q3 47.7%  2025Q4 54.5%
                                             2026Q1 45.2%  2026Q2 65.9%

Consistent across years and halves, but swings 45%-75% by quarter.

**Control:** plain gold fade with no alignment = 54.93%. Alignment adds **+3.02
points**. So most of the effect is gold's own daily mean-reversion, not the
3-asset alignment.

## Why 57.94% accuracy still earns nothing

This is the important finding, and it applies to every result above.

    when RIGHT (124 trades): average gold move captured = 0.9223%
    when WRONG  (90 trades): average gold move lost     = 1.1462%
    -> losses are 1.24x LARGER than wins

    break-even accuracy required at this payoff: 55.4%
    actual accuracy:                             57.9%
    margin:                                      +2.5 points

Net over 19.5 months: **+11.21%** total gold movement captured, **t = +0.57** —
statistically indistinguishable from zero.

Sized to respect DD<5% with real costs: **k=0.2x -> +0.10%/month.**

The signal is right more often than it is wrong, but it is wrong when gold moves
big. High accuracy with negative skew is not an edge. **This is why hit-rate is
the wrong thing to hunt for.**

## Multiple-testing

XAUUSD fade raw p = 0.0201. Roughly 200 currency x signal x filter tests were run;
Bonferroni requires p < 2.5e-4. **It fails.** USDCHF and GBPUSD (n=75, single
year) fail by a wider margin.

## Conclusion

- No currency in 2025-2026 shows >80% accuracy on a pre-alignment signal. Ceiling **61.3%**.
- The only multi-year candidate, XAUUSD alignment-fade at 57.94%, has losses 1.24x
  its wins and t=+0.57 — worth **+0.10%/month** at <5% DD.
- 7 of 10 pairs have only 2026 data because the `majors/` 2025 files are empty.

**Getting real 2025 data for the other 7 pairs is the single highest-value next
step** — it would triple the sample on USDCHF and GBPUSD, the two most interesting
leads. I can fetch it through the same verified Investing.com pipeline used for
the core 3.

Reproduce: `research.inventory`, `research.percurrency`, `research.goldfade`, `research.winsize`
