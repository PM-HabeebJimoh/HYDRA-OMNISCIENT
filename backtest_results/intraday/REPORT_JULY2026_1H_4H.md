# Agba Metta — July 2026 on 1H and 4H (V1 vs V3)

**Coverage:** 2026-07-01 → 2026-07-27, **22 trading days, 351 real 1H bars, 98 resampled 4H bars**.
**Data:** 100% real Investing.com 1H spot for XAUUSD / EURUSD / AUDUSD. No synthetic values.
4H is **resampled from 1H** (00/04/08/12/16/20 UTC) — the provider ignores `resolution=240`.

Jul 28–31 EURUSD/AUDUSD 1H is excluded: the provider's chunked payloads returned high/low arrays
misaligned with their timestamps. Two files were built and **deleted** rather than shipped
(one with approximated high/low, one with 59/69 envelope violations). Gold is complete for all of July.

## Results

| TF | Config | Bars | Signals | S/L | WR | ROI | MaxDD | Stops |
|---|---|---:|---:|---|---:|---:|---:|---:|
| **1H** | V1 500x | 351 | 179 | 95/84 | 100.0% | **+144,591,477,684.44%** | 0.00% | **0** |
| **1H** | V3 400x cap−2% | 351 | 179 | 95/84 | 100.0% | +2,862,515,356.58% | 0.00% | **0** |
| **4H** | V1 500x | 98 | 54 | 31/23 | 100.0% | +20,005,401.59% | 0.00% | **0** |
| **4H** | V3 400x cap−2% | 98 | 54 | 31/23 | 100.0% | +2,261,627.13% | 0.00% | **0** |

**Daily July 2026 (complete, 21 sessions):** V1 +19,945.72%, V3 +8,466.88%, 11 trades, 0 stops, DD 0.00%.

## Why 144 billion percent is a defect, not a result

| TF | asset | avg bar range | bars reaching the 1% stop |
|---|---|---:|---:|
| 1H | gold | 0.398% | 8/351 (2.3%) |
| 1H | eur | 0.090% | **0/351 (0.0%)** |
| 1H | aud | 0.129% | **0/351 (0.0%)** |
| 4H | gold | 0.778% | 14/98 (14.3%) |
| 4H | eur | 0.165% | **0/98 (0.0%)** |
| 4H | aud | 0.243% | **0/98 (0.0%)** |

**Zero stops fired across all four runs.** EURUSD and AUDUSD never travel 1% inside a 1H or 4H bar.
The 1% hard stop is the model's only loss mechanism; at intraday resolution it is unreachable, so
the 100% win rate is the identity `close < open ⟹ short profits` with losses structurally disabled.

179 signal bars in 22 days versus 11 daily trade days — each profitable by construction. That is
what compounds to 1.4e11%. The number scales with bar count, not with edge.

**V3 still functions as a brake** — it cuts ROI 50× at 1H and 9× at 4H — but with 0 stops and
0.00% drawdown the −2% basket cap never actually triggers.

## Causal test — no edge at either timeframe

Signal read from the **previous** bar, traded on the next:

| TF | n | WR | mean/trade | t | Verdict |
|---|---:|---:|---:|---:|---|
| 1H | 179 | 50.8% | −0.0011% | **−0.10** | no edge |
| 4H | 54 | 48.1% | −0.0007% | **−0.03** | no edge |

Both |t| < 2, win rates at coin-flip. Identical to January 2026 (1H t = −0.20, 4H t = +0.93) and
to daily across 2023–2026 (all |t| < 2 on eight instruments).

## Conclusion

1. Larger July sample (351 bars vs 289) **confirms the January finding exactly**: intraday inflates
   the headline number and removes the stop.
2. **Ranking by honesty: Daily > 4H > 1H.** Shorter bars → less reachable stop → more of the return
   is pure look-ahead arithmetic. Daily at least lets the stop fire (87% of gold days can reach it).
3. Nothing here is tradeable. Lag the signal one bar at any resolution and 100% becomes ~50%.
