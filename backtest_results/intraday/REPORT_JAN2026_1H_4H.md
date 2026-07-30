# Agba Metta — January 2026 on 1H and 4H (V1 vs V3)

**Window:** 2026-01-01 → 2026-01-14 (140 aligned 1H bars, 40 resampled 4H bars).
**Data:** 100% real Investing.com 1H spot for XAUUSD / EURUSD / AUDUSD.
**4H is resampled from 1H** — the provider silently ignores `resolution=240` and returns
hourly timestamps, so genuine 4H bars must be built from 1H (00/04/08/12/16/20 UTC buckets).

Rules unchanged from daily: all-3-DOWN = SHORT, all-3-UP = LONG, entry = bar open,
exit = bar close, 1% hard stop intrabar, 20% risk/bar, equal weight /3.
V1 = 500x no cap. V3 = 400x + basket −2% per-bar loss cap.

## Results

| TF | Config | Bars | Signals | S/L | WR | ROI | MaxDD | Stops |
|---|---|---:|---:|---|---:|---:|---:|---:|
| **1H** | V1 500x | 140 | 60 | 29/31 | 100.0% | **+80,182.89%** | 0.00% | **0** |
| **1H** | V3 400x cap−2% | 140 | 60 | 29/31 | 100.0% | +22,728.22% | 0.00% | **0** |
| **4H** | V1 500x | 40 | 15 | 6/9 | 100.0% | +1,735.62% | 0.00% | **0** |
| **4H** | V3 400x cap−2% | 40 | 15 | 6/9 | 100.0% | +978.89% | 0.00% | **0** |

Daily reference (full Jan 2026): V1 +16,817.41%, V3 +7,419.03%, DD 0.00%, 11 signal days.

## The finding that matters: intraday DISABLES the stop

| TF | asset | avg bar range | bars where 1% stop is reachable |
|---|---|---:|---:|
| 1H | gold | 0.366% | **1/140 (0.7%)** |
| 1H | eur | 0.093% | **0/140 (0.0%)** |
| 1H | aud | 0.133% | **0/140 (0.0%)** |
| 4H | gold | 0.690% | 3/40 (7.5%) |
| 4H | eur | 0.178% | **0/40 (0.0%)** |
| 4H | aud | 0.240% | **0/40 (0.0%)** |
| Daily | gold | — | 130/149 (87.2%) |
| Daily | aud | — | 35/149 (23.5%) |
| Daily | eur | — | 9/149 (6.0%) |

**Zero stops fired in any intraday run.** On 1H bars EUR and AUD literally never travel 1%
from the open, and gold does so 0.7% of the time. The 1% hard stop — the model's only loss
mechanism — is mathematically unreachable at intraday resolution.

So the 100% win rate at 1H/4H is not a market result. It is the identity
`close < open ⟹ short profits`, with the sole loss channel switched off. The daily timeframe
at least let the stop fire (87% of gold days can reach it, 12 stop-outs observed in 2025+2026).
**Moving to intraday makes the model structurally more fictitious, not more profitable.**

## Signal frequency inflates the compounding illusion

| TF | Alignment rate | Projected signal bars/yr |
|---|---:|---:|
| 1H | 42.9% | ~2,674 |
| 4H | 37.5% | ~585 |
| Daily | 56.4% | ~84 |

1H fires ~32× more often than daily. Since every signal bar is profitable by construction,
compounding accelerates ~32×: +80,183% in nine trading days at 1H versus +16,817% in a full
month at daily. Extrapolated over a year the 1H figure exceeds 10^130 — a number with no
physical meaning, which is itself the proof that this is not tradeable return.

## Causal test — the edge still does not exist

Signal read from the **previous** bar, traded on the next:

| TF | n | WR | mean/trade | t | Verdict |
|---|---:|---:|---:|---:|---|
| 1H | 60 | 48.3% | −0.0027% | −0.20 | **no edge** |
| 4H | 15 | 66.7% | +0.0327% | +0.93 | **no edge** |

Neither reaches significance. Identical to the daily result (t = +0.11 to +1.33 across all
instruments and timeframes tested). Lagging the signal by one bar collapses a "100% win rate"
into a coin flip at every resolution.

## Conclusion

1. Both V1 and V3 "work" better on paper at 1H — V1 returns +80,183% in nine days — and both
   are less real than the daily version.
2. **V3 keeps its intended role:** it cuts ROI roughly 3.5× (80,183% → 22,728% at 1H;
   1,736% → 979% at 4H) as a risk brake. But with 0 stops and 0.00% DD at these timeframes,
   there is no risk for it to brake, so the cap never activates.
3. Ranking by honesty: **Daily > 4H > 1H.** The shorter the bar, the less reachable the stop,
   the more the 100% win rate is pure look-ahead arithmetic.
4. Nothing here changes the causal conclusion: at 1H, 4H and daily, lag-1 |t| < 2 — no edge.
