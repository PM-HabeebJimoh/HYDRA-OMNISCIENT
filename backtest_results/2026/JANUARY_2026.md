# Agba Metta Model — January 2026 Backtest

100% real market data. 20 real trading sessions, 2026-01-02 → 2026-01-30.

```bash
python3 scripts/run_monthly_backtest.py   # January is the first month in the run
```

---

## Result

| Metric | Value |
|---|---:|
| Initial capital | $100,000 |
| **Final equity** | **$148,294.21** |
| **Total return** | **+48.29%** |
| Trade days | 4 of 20 sessions |
| Day win rate | 75.00% (3/4) |
| Asset trades | 12 |
| Asset win rate | 83.33% (10/12) |
| Profit factor | 1.58 |
| Max drawdown | −19.67% |
| Sharpe ratio | 3.73 |

---

## Daily loop trace

Every session was CONTRACTION (real yield 1.86–1.97%, all > 0.7%), so the model
looked for all-three-DOWN alignment on each day.

| Date | Yield | Gold | EUR | AUD | Aligned | Action |
|---|---:|---|---|---|---|---|
| 2026-01-02 | 1.94% | DOWN | DOWN | UP | no | Skip |
| 2026-01-05 | 1.91% | UP | UP | UP | no | Skip |
| 2026-01-06 | 1.91% | UP | DOWN | UP | no | Skip |
| **2026-01-07** | **1.88%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |
| **2026-01-08** | **1.92%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |
| 2026-01-09 | 1.90% | UP | DOWN | DOWN | no | Skip |
| 2026-01-12 | 1.90% | UP | UP | UP | no | Skip |
| 2026-01-13 | 1.88% | UP | DOWN | DOWN | no | Skip |
| 2026-01-14 | 1.86% | UP | DOWN | DOWN | no | Skip |
| 2026-01-15 | 1.88% | UP | DOWN | UP | no | Skip |
| 2026-01-16 | 1.91% | DOWN | UP | DOWN | no | Skip |
| 2026-01-20 | 1.97% | UP | UP | UP | no | Skip |
| 2026-01-21 | 1.92% | DOWN | DOWN | UP | no | Skip |
| 2026-01-22 | 1.95% | UP | UP | UP | no | Skip |
| 2026-01-23 | 1.92% | UP | UP | UP | no | Skip |
| 2026-01-26 | 1.90% | DOWN | UP | FLAT | no | Skip |
| 2026-01-27 | 1.90% | FLAT | UP | UP | no | Skip |
| 2026-01-28 | 1.90% | FLAT | DOWN | UP | no | Skip |
| **2026-01-29** | **1.89%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |
| **2026-01-30** | **1.90%** | **DOWN** | **DOWN** | **DOWN** | **YES** | **TRADE** |

4 aligned days out of 20. Note 2026-01-26/27/28: gold or AUD closed exactly flat
(`close == open`), which is not DOWN, so alignment correctly fails.

---

## Trade blotter

All SHORT (CONTRACTION regime). Stop = entry × 1.01, checked intraday against the high.

| Date | Asset | Entry | Stop | Exit | Return | PnL | Exit reason |
|---|---|---:|---:|---:|---:|---:|---|
| 01-07 | XAUUSD | 4450.00000 | 4494.50000 | 4449.29980 | +0.02% | +$524 | CLOSE |
| 01-07 | EURUSD | 1.16970 | 1.18140 | 1.16885 | +0.07% | +$2,422 | CLOSE |
| 01-07 | AUDUSD | 0.67370 | 0.68044 | 0.67285 | +0.13% | +$4,206 | CLOSE |
| 01-08 | XAUUSD | 4460.20020 | 4504.80220 | 4449.70020 | +0.24% | +$8,408 | CLOSE |
| 01-08 | EURUSD | 1.16820 | 1.17988 | 1.16545 | +0.24% | +$8,408 | CLOSE |
| 01-08 | AUDUSD | 0.67235 | 0.67907 | 0.66940 | +0.44% | +$15,671 | CLOSE |
| 01-29 | XAUUSD | 5415.70020 | 5469.85720 | 5469.85720 | −1.00% | −$46,547 | **STOP_LOSS** |
| 01-29 | EURUSD | 1.19875 | 1.21074 | 1.19605 | +0.23% | +$10,484 | CLOSE |
| 01-29 | AUDUSD | 0.70405 | 0.71109 | 0.70275 | +0.18% | +$8,595 | CLOSE |
| 01-30 | XAUUSD | 5376.39990 | 5430.16390 | 5430.16390 | −1.00% | −$37,391 | **STOP_LOSS** |
| 01-30 | EURUSD | 1.19800 | 1.20998 | 1.18770 | +0.86% | +$32,147 | CLOSE |
| 01-30 | AUDUSD | 0.70505 | 0.71210 | 0.69725 | +1.11% | +$41,366 | CLOSE |

Two gold stop-outs (01-29, 01-30): gold rallied against the short and tagged the
1% stop intraday, exiting at the stop price.

---

## Compounding

| Date | Start equity | Position/asset | Notional | Daily PnL | End equity | Return |
|---|---:|---:|---:|---:|---:|---:|
| 2026-01-07 | $100,000 | $6,667 | $3,333,333 | +$7,152 | $107,152 | +7.2% |
| 2026-01-08 | $107,152 | $7,143 | $3,571,746 | +$32,488 | $139,640 | +30.3% |
| 2026-01-29 | $139,640 | $9,309 | $4,654,676 | −$27,468 | $112,172 | −19.7% |
| 2026-01-30 | $112,172 | $7,478 | $3,739,071 | +$36,122 | **$148,294** | +32.2% |

Position per asset = `equity × 20% / 3`; notional = position × 500.
Independently recomputed from the raw panel — matches the engine to the cent.

The −19.7% day on 01-29 is the month's max drawdown. Under the Agba Metta daily
loop there is no halt, so 01-30 traded normally and recovered the month to +48.29%.

---

## Data

| Series | Instrument | Source |
|---|---|---|
| `gold` | COMEX front-month gold future | Yahoo Finance `GC=F` |
| `eur` | CME front-month Euro FX future | Yahoo Finance `6E=F` |
| `aud` | CME front-month AUD future | Yahoo Finance `6A=F` |
| `real_yield` | 10Y TIPS constant-maturity real yield | FRED `DFII10` |

Raw payloads cached verbatim in `data/raw/`. All bars validated
`low ≤ open, close ≤ high`. Futures are used rather than spot because the
available spot FX feed returns `open ≈ close` bars, which is degenerate for a
`close − open` alignment filter.

**Artefacts:** `trades_2026-01.csv`, `equity_2026-01.csv`
