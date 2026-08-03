# Hunting ROI > 1000% under live-correct timing — result

All runs: signal read on a **closed** bar → enter **next** bar's open → 1% stop
from actual entry → exit that bar's close. No basket loss cap anywhere. 100% real
Investing.com bars, Dec 2025 – Jul 2026.

## Search 1 — the standard model, 864 configurations

7 months × 3 timeframes × follow/fade × stop on/off × leverage 100–2000.

**ROI > 1000%: 0 of 864.** Best per month/TF, leverage tuned:

| best cells | ROI | maxDD |
|---|---:|---:|
| May26 4H FOLL 500x | +865.99% | −75.67% |
| Jan26 4H FOLL 400x | +603.23% | −73.09% |
| Jan26 DAILY FOLL 750x | +347.10% | −76.93% |

## Search 2 — widened to 259,200 configurations

Leverage 25–3000 in steps of 25, 9 stop levels (0–5%), 5 risk fractions (20–100%).

**ROI > 1000%: 0 of 259,200.** Global best: Jan26 4H FOLL, k=100, risk 1.00,
stop 0.50% → **+897.24%**, maxDD −76.64%.

## Why the basket has a ceiling

Equity compounds: `E = Π(1 + k·rᵢ)`. Raising leverage scales **every** bar's
return — wins *and* losses. The derivative of log-equity, `Σ rᵢ/(1+k·rᵢ)`, is
strictly decreasing in k and crosses zero once. Past that point more leverage
**lowers** final equity, and once `k·|worst rᵢ| ≥ 1` the account is wiped in a
single bar. ROI is bounded by the edge in `r`, not by leverage.

Hindsight-optimal leverage per month/TF confirms it — the highest value reachable
anywhere on the basket, with perfect foresight of the best k, is **+897.33%**.

## Search 3 — beyond the basket

| avenue | best result |
|---|---:|
| 8-month compound, one fixed basket config | +55.15% |
| **Single instrument: EURUSD 1H FADE, k=71.5** | **+1,456.66%** |
| 8 best months compounded with full hindsight | +1,421,783% (unattainable) |

## The one config that clears 1000% — and it survives testing

**EURUSD alone, 1H, fade the 3-asset alignment, k=71.5, no stop, Dec25–Jul26:**

```
1834 trades   win rate 49.02%   mean +0.00417%/trade   t = +2.34
ROI +1,456.66%   maxDD -79.82%
```

| test | result |
|---|---|
| **Leverage sensitivity** | smooth curve: k=40→811%, 60→1350%, **71.5→1457%**, 90→1182%, 120→301%. No spike — a broad optimum, not a fitted point. |
| **Split-half** | first half +391.59% (t=+1.80), second half +216.66% (t=+1.51). Positive in both. |
| **Per month** | 6 of 8 positive: Dec +332%, Jan +17%, Feb −44%, Mar +34%, Apr +206%, May −3%, Jun +24%, Jul +11%. |
| **Selection-noise null** | best-of-search on 120 sign-flipped runs: median 86.71%, 95th pct 1,096.28%. Actual 1,456.66% → **p = 0.042, passes**. |

This is the first result in the entire project to clear a proper noise null.

## The decisive gate: real costs

1,834 round trips at k=71.5 is enormous turnover. Applying real EURUSD costs:

| scenario | cost | net/trade | best k | 8-mo ROI |
|---|---:|---:|---:|---:|
| zero cost (unrealistic) | 0.0000% | +0.00417% | 71.5 | **+1,456.66%** |
| institutional ECN 0.1 pip | 0.0010% | +0.00317% | 54.5 | +390.45% |
| tight retail ECN 0.2 pip | 0.0020% | +0.00217% | 37.5 | +110.91% |
| typical retail ECN 0.3 pip | 0.0030% | +0.00117% | 20.0 | +24.26% |
| retail standard 0.5 pip | 0.0050% | −0.00083% | — | **−0.77%** |
| retail wide 1.0 pip | 0.0100% | −0.00583% | — | −5.22% |

**Break-even cost = 0.417 pips.** The edge is 0.417 pips per trade; a realistic
all-in EURUSD round trip is 0.3–0.5 pips.

## Verdict

**+1,456.66% is achievable on this real data at zero cost, and the signal passes
a proper selection-noise null (p = 0.042).** That is a genuine finding, and it is
the target you asked for.

It is **not tradeable as-is.** The edge is 0.417 pips and dies at ~0.5 pip
all-in cost. It also runs a −79.82% drawdown, and 62% of the return comes from
two months (Dec +332%, Apr +206%).

The honest statement: **>1000% exists in this data only in the zero-cost limit.**
At institutional cost the same signal gives +390%; at typical retail it gives
+24%; at standard retail it loses money.

The real lever is now **cost, not leverage** — every 0.1 pip saved is worth
hundreds of percent here. That is a concrete, testable direction if you want to
pursue it.

Reproduce: `research.hunt1000`, `research.hunt1000b`, `research.ceiling1000`,
`research.hunt1000c`, `research.verify1456`, `research.costs1456`
