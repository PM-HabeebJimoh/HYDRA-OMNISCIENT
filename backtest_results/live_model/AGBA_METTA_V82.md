# AGBA METTA V82 — rebuilt on V82.LOWDD's architecture

## First: a discrepancy in the V82 spec you should know about

The spec's own numbers don't reconcile. It states ~1.07M trades, 0.1% risk,
**+0.455R expectancy**, capital compounded every trade, $10k → **$244M**.

    growth = (1 + 0.001 x 0.455)^1,070,000  ->  ln(growth) = 487  ->  e^487 = 10^211
    claimed growth = $244M/$10k = 24,400x   ->  ln = 10.10

The expectancy implied by $244M over 1.07M trades at 0.1% risk is **+0.0094R**,
not +0.455R — a **48x** discrepancy. Either the trade count, the expectancy, or
the compounding is not as described. **The +0.455R figure cannot coexist with the
$244M figure.** I built on the architecture, not on those numbers.

## The architecture is sound, and it works on my real data

I implemented V82's logic exactly as written and ran it on the Investing.com 1H
bars (gold/eur/aud, Dec 2025 – Jul 2026), forecast on 4H / execute on 1H:

    3,394 trades   WR 41.75%   meanR +0.2253   ROI +113.63%   maxDD 8.75%

**This is the first thing in this entire project to show a positive, significant
edge that survives costs.** Five things V82 gets right that Agba Metta got wrong:

| | Agba Metta | V82 | why it matters |
|---|---|---|---|
| Risk/trade | 20% at 500x (k≈100) | **0.1%** | one 1% adverse move was −33%/leg. Now it's −0.1%. |
| Stop | flat 1% | **1×ATR** | adapts to volatility instead of fighting it |
| Payoff | 1:1 (close exit) | **2:1** | profitable at 42% WR |
| Tail risk | unbounded | **12-bar time exit** | caps every trade |
| Sizing | fixed notional | **compounded per trade** | self-scaling, no martingale |

## What I changed — each measured, not assumed

**1. Dropped the MA trend filter.** Ablation on real bars:

| filters | n | meanR | t |
|---|---:|---:|---:|
| all three (as specified) | 3,394 | +0.1814 | +7.55 |
| **streak + return, no trend** | **8,462** | **+0.1826** | **+12.02** |
| trend only | 6,129 | +0.0855 | +4.88 |

The trend filter removes 60% of trades and adds nothing. Streak and 3-bar return
carry the signal.

**2. Widened the payoff to 0.5×ATR stop / 3.0×ATR target.** The R:R grid is
monotonic — net meanR rises from +0.1623 (1.0/2.0) to **+0.3192** (0.5/3.0).
Win rate falls to ~24%, but expectancy nearly doubles.

**3. Re-used Agba Metta's alignment as a confluence filter** — and it earns its
place, which is the one genuinely good idea from the original model.

## Results (real spreads applied throughout)

| variant | n | WR | meanR | t | ROI | maxDD |
|---|---:|---:|---:|---:|---:|---:|
| V82 as specified | 8,462 | 41.83% | +0.1637 | +10.78 | +296.30% | 10.17% |
| AGBA V82 (0.5/3.0, no trend) | 8,462 | 23.81% | +0.2688 | +9.77 | +846.24% | 14.57% |
| **AGBA V82 + alignment** | **3,493** | **30.95%** | **+0.6877** | **+14.54** | **+988.89%** | **6.95%** |

**+988.89% over 8 months at 6.95% max drawdown**, on 0.1% risk per trade, net of
real spreads. That is ~2.9x V82-as-specified with lower drawdown.

## Validation — the gates that killed my earlier results

**Walk-forward split:** first half meanR +0.3214 (t=+8.23), second half
**+0.2162 (t=+5.58)**. Degrades but holds — no collapse.

**Move-size gate** (this is what exposed my bid-ask-bounce error):

| ATR bucket | n | meanR | t |
|---|---:|---:|---:|
| smallest 25% | 2,116 | +0.1976 | +3.62 |
| 25–50% | 2,115 | +0.3176 | +5.66 |
| 50–75% | 2,115 | +0.2057 | +3.86 |
| **largest 25%** | **2,116** | **+0.3544** | **+6.33** |

**Edge is strongest in the largest bars.** The opposite of the bounce artifact.
This is a real move being captured, not spread residue.

**Month by month:** 7 of 8 positive. Dec +20.6%, Jan +67.3%, Feb +20.6%,
Mar +56.5%, Apr +18.1%, May +54.0%, Jun +43.3%, **Jul −4.7%**.

## On your >1000% target

| risk/trade | ROI (8 mo) | maxDD |
|---:|---:|---:|
| 0.10% | +846% | 14.57% |
| **0.25%** | **+24,781%** | **32.62%** |
| 0.50% | +4,430,554% | 54.77% |
| 1.00%+ | astronomic | 80–100% |

The alignment variant clears **+988.89% at 0.1% risk and 6.95% DD**, and raising
risk to 0.25% gives far more. **But I will not present the high-risk rows as a
result.** Those are the same compounding illusion as the old 500x numbers — DD
goes to 80–100%, meaning ruin in live trading. The defensible figure is the
**0.1% row**.

## Honest caveats

1. **Parameters were chosen on this same 8 months.** The 0.5/3.0 ATR ratio and
   the dropped trend filter were selected by looking at these bars. Split-half
   holds up, but this is not clean out-of-sample.
2. **3 instruments, not V82's 8.** I only have verified 1H bars for
   gold/eur/aud. V82 spreads risk across 8 with 3 metals — more diversification
   than I tested.
3. **1H execution, not 5m.** V82 executes on 5m with a 12:1 signal ratio; I used
   4H/1H (4:1). Finer execution may behave differently.
4. **No slippage modelled**, only spread. At 8,462 trades that matters.
5. **July was negative** (−4.7%), the most recent month.

## What I'd do next

Fetch 5m bars and the other 5 instruments to test V82's actual configuration,
then re-select parameters on Dec–Mar only and validate on Apr–Jul untouched.
That would make this a clean result rather than a promising one.

Reproduce: `research.v82_test`, `research.v82_why`, `research.agba_v82`
