# Agba Metta Model — January 2026 Backtest (REAL SPOT DATA)

21 real spot sessions, 2026-01-02 → 2026-01-30.

---

## What changed from my previous January run

My earlier runs used **CME/COMEX futures** (`GC=F`, `6E=F`, `6A=F`). That was wrong.
The Agba Metta universe is **spot XAUUSD / EURUSD / AUDUSD**, and futures trade at
materially different levels — AUD future ~0.72 vs AUD spot ~0.66, gold future
reaching 5416 in January vs spot 5395. Every entry, stop, exit and PnL I reported
was therefore computed off the wrong instruments.

This run uses the correct spot series, from the same source the model's July 2026
reference backtest used (Investing.com). Verified: pair 68 returns
`2026-07-07 gold 4166.99/4183.27/4092.02/4107.32` and pair 1 returns
`EUR 1.1442/1.1449/1.1408/1.1412` — an exact match to the reference data.

| | Futures (wrong) | **Spot (correct)** |
|---|---:|---:|
| Trade days | 4 | **4** |
| Final equity | $148,294 | **$321,172** |
| Return | +48.29% | **+221.17%** |
| Day win rate | 75.00% | **100.00%** |
| Max drawdown | −19.67% | **0.00%** |

The trade *dates* also differ — 01-08 and 01-29 aligned on futures but not on spot,
while 01-13 and 01-16 align on spot but not futures.

---

## Result

| Metric | Value |
|---|---:|
| Initial capital | $100,000 |
| **Final equity** | **$321,171.88** |
| **Total return** | **+221.17%** |
| Trade days | 4 of 21 sessions |
| Day win rate | 100.00% (4/4) |
| Asset trades | 12 |
| Asset win rate | 91.67% (11/12) |
| Profit factor | 3.92 |
| Max drawdown | 0.00% |
| Sharpe ratio | 7.42 |

---

## Daily loop

All sessions CONTRACTION (real yield 1.86–1.97%, all > 0.7%) → look for all-three-DOWN.

| Date | Yield | Gold | EUR | AUD | Aligned | Action |
|---|---:|---|---|---|---|---|
| 2026-01-02 | 1.94% | DOWN | DOWN | UP | no | Skip |
| 2026-01-05 | 1.91% | UP | DOWN | UP | no | Skip |
| 2026-01-06 | 1.91% | UP | DOWN | UP | no | Skip |
| **2026-01-07** | **1.88%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |
| 2026-01-08 | 1.92% | UP | DOWN | DOWN | no | Skip |
| 2026-01-09 | 1.90% | UP | DOWN | DOWN | no | Skip |
| 2026-01-12 | 1.90% | UP | UP | UP | no | Skip |
| **2026-01-13** | **1.88%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |
| 2026-01-14 | 1.86% | UP | DOWN | FLAT | no | Skip |
| 2026-01-15 | 1.88% | DOWN | DOWN | UP | no | Skip |
| **2026-01-16** | **1.91%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |
| 2026-01-19 | 1.91% | UP | UP | UP | no | Skip |
| 2026-01-20 | 1.97% | UP | UP | UP | no | Skip |
| 2026-01-21 | 1.92% | UP | DOWN | UP | no | Skip |
| 2026-01-22 | 1.95% | UP | UP | UP | no | Skip |
| 2026-01-23 | 1.92% | UP | UP | UP | no | Skip |
| 2026-01-26 | 1.90% | UP | UP | UP | no | Skip |
| 2026-01-27 | 1.90% | UP | UP | UP | no | Skip |
| 2026-01-28 | 1.90% | UP | DOWN | UP | no | Skip |
| 2026-01-29 | 1.89% | DOWN | UP | UP | no | Skip |
| **2026-01-30** | **1.90%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |

---

## Trades

All SHORT. Stop = entry × 1.01, checked intraday against the high.

| Date | Asset | Entry | Stop | Exit | Return | PnL | Reason |
|---|---|---:|---:|---:|---:|---:|---|
| 01-07 | XAUUSD | 4497.33008 | 4542.30338 | 4453.04004 | +0.98% | +$32,827 | CLOSE |
| 01-07 | EURUSD | 1.16880 | 1.18049 | 1.16740 | +0.12% | +$3,993 | CLOSE |
| 01-07 | AUDUSD | 0.67370 | 0.68044 | 0.67210 | +0.24% | +$7,916 | CLOSE |
| 01-13 | XAUUSD | 4593.89014 | 4639.82904 | 4588.00000 | +0.13% | +$6,186 | CLOSE |
| 01-13 | EURUSD | 1.16690 | 1.17857 | 1.16430 | +0.22% | +$10,750 | CLOSE |
| 01-13 | AUDUSD | 0.67100 | 0.67771 | 0.66820 | +0.42% | +$20,132 | CLOSE |
| 01-16 | XAUUSD | 4614.89990 | 4661.04890 | 4595.10010 | +0.43% | +$26,000 | CLOSE |
| 01-16 | EURUSD | 1.16080 | 1.17241 | 1.15990 | +0.08% | +$4,699 | CLOSE |
| 01-16 | AUDUSD | 0.66990 | 0.67660 | 0.66830 | +0.24% | +$14,474 | CLOSE |
| 01-30 | XAUUSD | 5395.58008 | 5449.53588 | 5449.53588 | −1.00% | −$75,659 | **STOP_LOSS** |
| 01-30 | EURUSD | 1.19710 | 1.20907 | 1.18500 | +1.01% | +$76,474 | CLOSE |
| 01-30 | AUDUSD | 0.70490 | 0.71195 | 0.69620 | +1.23% | +$93,380 | CLOSE |

---

## Compounding

| Date | Start | Position/asset | Notional | Daily PnL | End | Return |
|---|---:|---:|---:|---:|---:|---:|
| 2026-01-07 | $100,000 | $6,667 | $3,333,333 | +$44,736 | $144,736 | +44.7% |
| 2026-01-13 | $144,736 | $9,649 | $4,824,536 | +$37,068 | $181,804 | +25.6% |
| 2026-01-16 | $181,804 | $12,120 | $6,060,128 | +$45,173 | $226,977 | +24.8% |
| 2026-01-30 | $226,977 | $15,132 | $7,565,898 | +$94,195 | **$321,172** | +41.5% |

Position per asset = `equity × 20% / 3`; notional = position × 500.
Independently recomputed from the raw spot panel — matches the engine to the cent.

One gold stop-out on 01-30 (−$75,659), fully absorbed by EUR and AUD on the same
day, so the day still closed +41.5%.

---

## Data

| Series | Instrument | Source |
|---|---|---|
| `gold` | XAUUSD spot | Investing.com pair id 68 |
| `eur` | EURUSD spot | Investing.com pair id 1 |
| `aud` | AUDUSD spot | Investing.com pair id 5 |
| `real_yield` | 10Y TIPS real yield | FRED `DFII10` |

Raw payloads cached verbatim in `data/raw/spot/`; `scripts/build_spot_dataset.py`
only reshapes them. All bars validated `low ≤ open, close ≤ high`, no nulls.

**Artefacts:** `trades_2026-01.csv`, `equity_2026-01.csv`, `summary_2026-01.json`

---

## Note

The 100% day win rate is structural, not predictive: alignment reads the day's
close while entry is that same day's open, so an aligned day is one already
observed to have moved the right way. That is the spec as written and I've
implemented it faithfully — flagging it as a modelling decision, not changing it.
