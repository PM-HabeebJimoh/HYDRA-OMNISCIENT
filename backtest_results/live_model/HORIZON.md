# THE FREQUENCY MISMATCH — A REAL HOLE I HAD NEVER TESTED

You said I was covering ~6% of the space. On one axis you were exactly right,
and it was a hole I had never noticed:

**Every direction test in this project predicted the NEXT BAR** — 1H, 4H, or
1 day. But the forces I kept naming as drivers — real yields, positioning, the
macro cycle — move on **weeks to months**. I was asking a quarterly variable to
forecast the next four hours. That is a frequency mismatch, and I had never
once tested the horizon these variables actually operate on.

I also fixed the coverage complaint: **7.6 years, not 8 months.**

## New data

| dataset | span | source |
|---|---|---|
| gold weekly, 348 bars | Jan 2019 – Sep 2025 | Investing.com |
| **DFII10 real 10y yield, 400 weeks** | Dec 2018 – Jul 2026 | FRED |
| CFTC gold positioning, 352 weeks | Dec 2018 – Aug 2025 | CFTC |

Covers COVID, the 2022 hiking cycle, the 2023 banking stress, and the 2024–25
bull. Multi-regime. Horizons tested: **1, 2, 4, 8, 13, 26 weeks.**

## The headline result

| signal | horizon | accuracy | t | sign-flip p |
|---|---|---|---|---|
| real yield < 52w median → long gold | 26w | 34.44% | **−7.13** | **0.0000** |
| " | 13w | 37.46% | −4.51 | 0.0000 |
| " | 8w | 42.71% | −3.98 | 0.0001 |

**t = −7.13.** The largest direction-related statistic in this entire project,
and it is **inverted from textbook theory** — a genuinely interesting finding.
And the horizon effect is real: naive t goes from ≈0 at next-bar to −7.13 at
26 weeks. **The macro layer does carry information at the horizon it actually
operates on.** That part I had been missing.

## Two corrections, and what survives

**Correction 1 — overlapping windows.** 26-week forward returns sampled weekly
overlap 25/26. Effective sample is 270/26 ≈ **11 independent observations**,
not 270. Naive t inflated by √26 = 5.1×.

| h | naive t | non-overlapping n | **honest t** |
|---|---|---|---|
| 4w | −3.01 | 73 | −1.55 |
| 8w | −3.98 | 36 | −0.90 |
| 13w | −4.51 | 22 | −0.95 |
| 26w | **−7.13** | **11** | **−1.65** |

**Correction 2 — the trend control, and this is the one that settles it.**
Gold went $1,287 → $3,587. Long-only at 26w is t=+14.61 with a 77.95% up-rate.
Splitting the two legs:

| leg | n | mean 26w return |
|---|---|---|
| LONG (real yield below median) | 109 | **+2.78%** |
| SHORT (real yield above median) | 161 | **+10.52%** |

**Both legs positive.** Gold rose in *both* regimes. The "short leg" isn't a
period when gold fell — it's the period when gold rose **fastest**. Shorting
there produced the large loss that generated t=−7.13.

So the finding is **not** "high real yields predict gold down." It is:

> **gold rose 3.8× faster when real yields were ABOVE their median** — the
> opposite of the textbook mechanism.

That is **beta timing** (how much of a trend you capture), not **direction**
(which way price goes). Both legs positive is the proof.

**Sub-period test confirms it is one episode, not a law:**

| period | h=26w excess | t |
|---|---|---|
| 2019–2022 | −2.37% | −1.00 (nothing) |
| 2022–2025 | −22.83% | −3.38 (the entire effect) |

The whole thing is 2022–2025: the Fed hiked real yields to 15-year highs and
gold rallied anyway, on central-bank buying and de-dollarisation.

## Why I am not trading the inversion

Flipping the sign gives "be long gold when real yields are high." But that is
long-only in a market up in 78% of all 26-week windows, resting on **11
independent observations**, from **one 3-year regime**, with **no theoretical
basis**, and it **directly contradicts the mechanism it was derived from**.

That is precisely the error I already made with COT positioning: in-sample
t=+2.36 → out-of-sample t=+0.57 on 352 weeks. Fitting a sign to one episode and
calling it a model. I won't repeat it four scripts later.

## What genuinely changed

**You were right about the frequency mismatch.** It was a real gap, it is now
closed, and it produced the strongest macro statistic in the project. That is
new knowledge:

- **Macro carries information at multi-week horizons that it does not carry at 4H.**
- **But it prices TREND PARTICIPATION, not direction.** Both legs positive.
- **Effective sample is the binding constraint.** 7.6 years of weekly data
  gives 11 independent 26-week windows. To get 50, I need ~25 years — which
  exists and I can fetch it.

**The honest scoreboard is unchanged: direction ~50%, magnitude 74–79%.**

## The one thing I'd do next that could move it

Not more angles — **more independent observations**. The 26-week test is
crippled by n=11, not by a lack of ideas. Two concrete fixes:

1. **Extend to 25 years** (2000–2026) → ~50 independent 26-week windows, and
   it would include 2013 and 2008 when real yields and gold moved the textbook
   way. That directly tests whether the 2022–25 inversion is a regime or noise.
2. **Run the same horizon test across 20+ instruments** — each adds independent
   windows. 20 assets × 11 windows = 220 observations, enough to actually
   resolve the question.

Both are reachable from here with the same fetch method. Say go and I'll run it.
