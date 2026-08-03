# June 2026 — Agba Metta, LIVE-CORRECT timing, FULL MONTH, all timeframes

Data: 100% Investing.com, fetched via the tvc4 history endpoint. No synthetic bars,
no interpolation, no envelope reconstruction. Every saved window validated with
`envelope_fixes = 0`.

## Coverage (this is what changed)

| Timeframe | Before | Now |
|---|---|---|
| Daily | Jun 1–30 (full) | Jun 1–30 (full) — unchanged |
| 1H | Jun 1–3 only, 55 bars | **Jun 1–30, 488 aligned bars, 26 trading days** |
| 4H | Jun 1–3 only, 15 bars | **Jun 1–30, 132 buckets** |

1H bars are counted after requiring XAUUSD + EURUSD + AUDUSD to all be present on
the same timestamp. 4H is resampled from 1H into 00/04/08/12/16/20 UTC buckets
(`resolution=240` is silently ignored by the provider and returns hourly stamps).

Raw windows added: `XAUUSD_2026jun_w2..w5`, `EURUSD_2026jun_w2a..w8a`,
`AUDUSD_2026jun_w2a..w8a` in `data/raw/intraday/`.

## Model timing

Signal candle closes → all 3 close UP = LONG, all 3 close DOWN = SHORT, mixed = skip
→ **enter on the NEXT candle open** → stop 1% from the ACTUAL entry price →
exit at that candle's close unless the stop hits first. 20% of equity split /3.

V1 = 500x, no cap. V3 = 400x with a −2% per-bar basket loss cap.

## Results

| TF | Config | Trades | S/L | WR | ROI | Max DD | Stops |
|---|---|---:|---|---:|---:|---:|---:|
| Daily | V1 500x | 12 | 7/5 | 16.7% | −99.87% | −99.87% | 10 |
| Daily | V3 400x cap−2% | 12 | 7/5 | 16.7% | +75.37% | −13.19% | 10 |
| 4H | V1 500x | 64 | 39/25 | 54.7% | −99.99% | −100.00% | 11 |
| 4H | V3 400x cap−2% | 64 | 39/25 | 54.7% | +3,001.34% | −7.75% | 11 |
| 1H | V1 500x | 260 | 145/115 | 52.3% | −91.72% | −98.46% | 6 |
| 1H | V3 400x cap−2% | 260 | 145/115 | 52.3% | +589,802.48% | −17.37% | 6 |

Daily V1 equity path: $100,000 → 47,059.94 → 26,332.88 → 16,003.25 → **971.73**
by 06-05 → ends **$134.75**.

## Raw edge, leverage stripped

Per-trade mean return of the 3-asset basket at 1x:

| TF | n | WR | mean/trade | t |
|---|---:|---:|---:|---:|
| Daily | 12 | 16.7% | −0.2608% | −1.79 |
| 4H | 64 | 54.7% | −0.0384% | −1.02 |
| 1H | 260 | 52.3% | +0.0049% | +0.51 |

None reach significance. The 1H t of +0.51 is noise; the 4H and Daily means are
negative.

## Random-direction control (the important test)

Take the exact bars where 3-asset alignment fires, then replace the signalled
side with a coin flip. 200 runs, seed 7.

| TF | Config | Actual | Random median | Random runs beating actual |
|---|---|---:|---:|---:|
| 1H | V1 500x | −91.72% | −97.25% | 72 / 200 |
| 1H | V3 400x cap−2% | +589,802% | +370,256% | **73 / 200** |
| 4H | V1 500x | −99.99% | −98.09% | 185 / 200 |
| 4H | V3 400x cap−2% | +3,001% | +9,461% | **172 / 200** |

Coin flips beat the real signal 37% of the time on 1H and 86% of the time on 4H.
The alignment rule adds nothing over random direction.

## What V3's huge number actually is

V3's +589,802% on 1H is not edge. It is the −2% cap truncating the left tail while
the right tail compounds unbounded at 400x. Random directions on the same bars
produce a median of +370,256% — same order of magnitude. Any sequence of
coin-flip trades under a hard loss cap and uncapped gains prints a large number.
V1, which is the same signal without the cap, loses 92% over the month.

## Bottom line

The full month of June 1H/4H data does not change the earlier conclusion, it
strengthens it with 10x the sample. Against the stated goals:

- Monthly ROI > 700%: only V3 reaches it, and the random control reproduces it.
- Max DD < 5%: not met anywhere. Best is 4H V3 at −7.75%; V1 configs are −98% to −100%.
- Live risk < 7%: a 1% stop at 400–500x is ~400–500% of allocated margin per leg.

Under honest next-candle timing the model has no measurable edge on June 2026 at
any of the three timeframes.
