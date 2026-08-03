# Effect of the Agba Metta 3-Asset Alignment on Other Currency Pairs

**Question:** when XAUUSD + EURUSD + AUDUSD all close the same direction, what happens
everywhere else in FX?

**Data:** 148 daily sessions, 2026-01-02 → 2026-07-28, all real Investing.com daily spot
(open→close). Cross-pairs fetched: GBPUSD (id 2), USDJPY (3), USDCHF (4), EURGBP (6),
USDCAD (7), NZDUSD (8), XAGUSD (69). Core panel is the existing verified 2026 spot file.

Regime split: **42 all-3-DOWN days · 41 all-3-UP days · 65 no-alignment days.**

## 1. Headline — the alignment is a DOLLAR event, not a gold/EUR/AUD event

On all-3-DOWN days (Agba Metta goes SHORT):

| Pair | mean % | median % | hit > 0 | stdev |
|---|---:|---:|---:|---:|
| GBPUSD | **−0.3919** | −0.3202 | 2.4 % | 0.2535 |
| NZDUSD | **−0.5616** | −0.6299 | 7.1 % | 0.4503 |
| USDJPY | **+0.2304** | +0.2115 | 92.9 % | 0.3176 |
| USDCHF | **+0.4012** | +0.3284 | 90.5 % | 0.3139 |
| USDCAD | **+0.2219** | +0.2252 | 81.0 % | 0.2286 |
| EURGBP | +0.0687 | +0.0636 | 69.0 % | 0.2024 |
| XAGUSD | **−4.3937** | −3.1343 | 7.1 % | 4.9777 |

On all-3-UP days (Agba Metta goes LONG) every sign flips cleanly:

| Pair | mean % | median % | hit > 0 | stdev |
|---|---:|---:|---:|---:|
| GBPUSD | **+0.4101** | +0.3470 | 97.6 % | 0.3111 |
| NZDUSD | **+0.5511** | +0.4973 | 87.8 % | 0.3944 |
| USDJPY | −0.2198 | −0.0250 | 46.3 % | 0.5510 |
| USDCHF | **−0.4869** | −0.3957 | 9.8 % | 0.4103 |
| USDCAD | −0.2210 | −0.2167 | 19.5 % | 0.2679 |
| EURGBP | −0.0715 | −0.0235 | 41.5 % | 0.2558 |
| XAGUSD | **+3.2477** | +2.4276 | 87.8 % | 2.9759 |

On no-alignment days everything collapses to noise (means −0.05 % to +0.12 %, hit rates 35–65 %).

## 2. The mechanism, isolated

Re-express every pair as a **USD return** (USDXXX as-is, XXXUSD negated; positive = USD up):

| Regime | n | mean USD move | USD-up frequency |
|---|---:|---:|---:|
| all-3-DOWN | 42 | **+1.0335 %** | **91.3 %** |
| all-3-UP | 41 | **−0.8561 %** | 16.3 % |
| no-alignment | 65 | −0.0673 % | 55.6 % |

**The 3-asset alignment is a broad USD-strength detector.** All three Agba Metta assets are
quoted against the dollar, so "all three down" is close to a tautology for "the dollar is up
today" — and that dollar move shows up in every other USD pair simultaneously.

**The decisive control is EURGBP** — the one pair with no USD leg. Its mean move is
+0.069 % / −0.072 % on aligned days versus −0.053 % on quiet days, and its amplitude ratio is
**1.00x**. A pair with no dollar exposure is completely unaffected. That is proof the effect is
carried by the dollar, not by some general risk factor.

## 3. Alignment days are volatility-expansion days

Mean absolute move, aligned days vs quiet days:

| Pair | aligned \|r\| | quiet \|r\| | ratio |
|---|---:|---:|---:|
| XAGUSD | 4.0295 | 1.9865 | **2.03x** |
| NZDUSD | 0.5954 | 0.3160 | **1.88x** |
| USDCHF | 0.4614 | 0.2725 | 1.69x |
| USDCAD | 0.2516 | 0.1516 | 1.66x |
| GBPUSD | 0.4023 | 0.2641 | 1.52x |
| USDJPY | 0.3194 | 0.2888 | 1.11x |
| **EURGBP** | 0.1714 | 0.1717 | **1.00x** |

Alignment does not merely predict direction — it selects days on which the whole dollar complex
moves **1.5–2x** its normal range. EURGBP again the flat control.

## 4. Beta to the Agba Metta basket

| Pair | beta | corr |
|---|---:|---:|
| XAGUSD | **+4.574** | +0.854 |
| NZDUSD | +0.482 | +0.680 |
| GBPUSD | +0.321 | +0.623 |
| USDCHF | −0.371 | −0.641 |
| USDJPY | −0.229 | −0.423 |
| USDCAD | −0.199 | −0.607 |
| EURGBP | −0.038 | −0.139 |

**Silver is the highest-octane expression of the signal** — 4.57x the basket's move, 0.854
correlation. NZDUSD is effectively a fourth AUDUSD (0.680 corr, same sign, bigger amplitude).
USDCHF is the cleanest inverse.

## 5. Per-pair edge if traded in the signal's implied USD direction

Same-day open→close, SHORT-basket day ⇒ buy USD, LONG-basket day ⇒ sell USD:

| Pair | n | mean % | win % | worst % | best % |
|---|---:|---:|---:|---:|---:|
| XAGUSD | 83 | **+3.8276** | 90.4 % | −2.3554 | +27.06 |
| NZDUSD | 83 | +0.5564 | 90.4 % | −1.0791 | +1.4895 |
| USDCHF | 83 | +0.4435 | 89.2 % | −0.2980 | +2.0713 |
| GBPUSD | 83 | +0.4009 | **97.6 %** | −0.0299 | +1.2132 |
| USDJPY | 83 | +0.2252 | 73.5 % | −0.9368 | +2.3937 |
| USDCAD | 83 | +0.2215 | 79.5 % | −0.2693 | +0.9486 |
| **EURGBP** | 83 | **−0.0700** | 34.9 % | −0.7270 | +0.5184 |

EURGBP is the only negative — exactly as predicted, since it carries no dollar.

## 6. Do the extra pairs improve the model? No.

| Basket | n | mean % | stdev | win % | mean/sd |
|---|---:|---:|---:|---:|---:|
| **core 3 (XAU/EUR/AUD)** | 83 | **+0.9033** | 0.6003 | **100.0 %** | **1.505** |
| cross 7 | 83 | +0.8007 | 0.6750 | 96.4 % | 1.186 |
| blended 10 | 83 | +0.8315 | 0.6317 | 100.0 % | 1.316 |

The original three are **already the best-conditioned expression** of the signal. Adding the
other seven lowers mean return, raises volatility and cuts risk-adjusted return from 1.505 to
1.186. The cross-pairs confirm and explain the signal; they do not improve it.

## 7. The same caveat still governs everything above

Reading the signal from the **prior** session instead of the same one:

| | n | mean % | win % | mean/sd |
|---|---:|---:|---:|---:|
| cross-7, same-day signal | 83 | +0.8007 % | 96.4 % | +1.186 |
| cross-7, lag-1 signal | 83 | **−0.0554 %** | 42.2 % | −0.078 |

The cross-pair co-movement is a **contemporaneous** fact about how the dollar moves — it is real,
large and highly consistent. It carries **no next-day predictive content**. So these pairs are
excellent for *confirmation and attribution* of what happened, and useless as a way to escape
the look-ahead constraint documented in the 4-year report.

## Bottom line

1. All-3-alignment = a broad USD move; 91.3 % of all USD-pair legs agree on direction.
2. EURGBP (no USD leg) is entirely unaffected — mean effect ~0.07 %, amplitude ratio 1.00x. This
   is the clean control that proves the dollar is the carrier.
3. Aligned days carry 1.5–2x normal volatility across the dollar complex.
4. XAGUSD is the strongest amplifier (beta 4.57, corr 0.854); NZDUSD behaves as a second AUDUSD;
   USDCHF is the cleanest inverse.
5. Adding these pairs to the trade **hurts** risk-adjusted performance (1.505 → 1.186).
6. None of it is predictive one session forward.
