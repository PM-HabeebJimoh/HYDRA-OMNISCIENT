# Agba Metta Model — Monthly Backtest, January–June 2026

Agba Metta Model only, run exactly per the specified daily loop.
100% real market data. No synthetic, interpolated or placeholder prices.

```bash
python3 scripts/build_dataset.py        # raw provider payloads -> clean panel
python3 scripts/run_monthly_backtest.py # month-by-month backtest
```

---

## 1. Engine validated against the July 2026 benchmark

Before running Jan–Jun, the engine was replayed against the reference July 2026
backtest. It reproduces that result **to the cent**:

| Day | Daily PnL | Equity | Reference |
|---|---:|---:|---|
| Jul 7 | +$71,635 | $171,635 | $171,635 ✓ |
| Jul 13 | +$180,643 | $352,279 | $352,279 ✓ |
| Jul 16 | +$293,974 | $646,253 | $646,253 ✓ |
| Jul 23 | +$480,155 | **$1,126,408** | **$1,126,408** ✓ |

Engine output: 4 trade days, final equity **$1,126,407.83**, +1026.41%.

Per-asset Jul 7 also matches exactly: XAU +1.43% → +$47,732, EUR +0.26% → +$8,740,
AUD +0.45% → +$15,163.

---

## 2. Rules as run

| Rule | Setting |
|---|---|
| Regime | real yield > 0.7% = CONTRACTION (short); < −0.1% = EXPANSION (long); else STABILITY (skip) |
| Alignment | all 3 assets must close in the regime direction, same day; else skip day |
| Entry / Exit | enter at that day's `open`, exit at that day's `close` |
| Sizing | `equity × 20% / 3 assets` = position per asset |
| Leverage | 500x → notional = position × 500 |
| Hard stop | `entry × 1.01` for SHORT (`× 0.99` for LONG), checked intraday vs high/low |
| Daily loop | **every aligned day is traded** — no halt step |

Verified in the output: stop/entry ratio is exactly `1.01` on every short;
position per asset is `equity × 0.20 / 3`; notional is `× 500`.

---

## 3. Three errors in my previous run — corrected

1. **Trade days were wrong (the big one).** I had added a max-drawdown/daily-loss
   *halt* that stopped trading after a breach. Your daily loop has no such step.
   That halt suppressed 26 of 29 aligned days and reported **3 trade days for H1
   instead of 29**, which cascaded into every other number. Removed — risk-limit
   breaches are now recorded for reporting only, never enforced.
2. **Monthly figures were downstream of the same bug** — Jan showed 3 trade days
   / +12.17%, actually 4 days / +48.29%; Feb showed 1 day / −21.05%, actually
   5 days / +336.52%.
3. **`signal_lag_days`** — an override I invented in an earlier pass that is not
   an Agba Metta rule. Already removed; alignment is same-day close vs open,
   entry at that day's open, as specified.

---

## 4. Results

Each month restarts from $100,000. The H1 row compounds across the half-year.

| Period | Sessions | Trade days | Return | Day WR | Max DD | Final equity |
|---|---:|---:|---:|---:|---:|---:|
| January 2026 | 20 | 4 | +48.29% | 75.00% | −19.67% | $148,294 |
| February 2026 | 19 | 5 | +336.52% | 80.00% | −21.05% | $436,516 |
| March 2026 | 22 | 7 | +13,893.39% | 100.00% | 0.00% | $13,993,391 |
| April 2026 | 21 | 5 | +944.05% | 100.00% | 0.00% | $1,044,052 |
| May 2026 | 20 | 4 | +481.93% | 100.00% | 0.00% | $581,926 |
| June 2026 | 21 | 4 | +1,293.16% | 100.00% | 0.00% | $1,393,155 |
| **2026 H1 (compounded)** | 123 | **29** | **+76,671,758.65%** | 93.10% | −21.05% | $76,671,858,646 |

29 trade days across H1, matching the independently counted 29 aligned days.

---

## 5. Data

| Series | Instrument | Source |
|---|---|---|
| `gold` | COMEX front-month gold future | Yahoo Finance `GC=F`, daily OHLC |
| `eur` | CME front-month Euro FX future | Yahoo Finance `6E=F`, daily OHLC |
| `aud` | CME front-month AUD future | Yahoo Finance `6A=F`, daily OHLC |
| `real_yield` | 10Y TIPS constant-maturity real yield | FRED `DFII10` |

**123 real sessions**, 2026-01-02 → 2026-06-30 (Jan 20, Feb 19, Mar 22, Apr 21,
May 20, Jun 21). Raw payloads cached verbatim in `data/raw/`; the build script
only reshapes them. All bars validated `low ≤ open, close ≤ high`, no nulls.
Yield join is as-of, so FRED holidays never inject future data.

The old loader had hardcoded placeholders (its "January 2026" gold prices were
`1.1732` — EUR/USD values in the gold field). Those are gone.

**One deviation, flagged:** the universe names spot `XAUUSD`/`EURUSD`/`AUDUSD`;
I used the corresponding futures because the available spot FX feed returns bars
where `open ≈ close`, which is degenerate for a `close − open` filter. Futures
carry genuine session OHLC. Spot at this granularity needs a paid provider — say
the word and I'll wire one in and re-run.

---

## 6. Two things worth your attention

- **The H1 compounded figure (+76.7 million %) is arithmetically correct but not
  realistic as a P&L.** It compounds 20% risk at 500x across a 27-of-29 winning
  streak, reaching $76.7bn — far beyond what the gold and FX markets could absorb.
  Position size is never capped against liquidity, and costs are zero
  (`commission_per_trade: 0.0`, `slippage_pct: 0.0`).
- **The 100% win-rate months are structural.** Alignment reads the day's close,
  entry is that same day's open — so on an aligned day the model enters in a
  direction the session has already been observed to move. This is exactly what
  the spec says, and I've implemented it as written, but it means those months
  measure the rule rather than a forecastable edge. Flagging it as a modelling
  decision for you, not changing it.

---

## 7. Artefacts

```
data/raw/                      raw provider payloads, cached verbatim
data/market_data_2026.json     clean 123-session panel
backtest_results/2026/
  monthly_summary.csv/.json    per-month + H1 metrics
  trades_<month>.csv           per-month trade blotters
  equity_<month>.csv           per-month daily equity curves
  trades_2026H1.csv            compounded run blotter
  equity_2026H1.csv            compounded run equity curve
```
