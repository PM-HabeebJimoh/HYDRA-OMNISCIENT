# Agba Metta Model — Monthly Backtest, January–June 2026

100% real market data. No synthetic, simulated, interpolated or placeholder prices.

Reproduce with:

```bash
python3 scripts/build_dataset.py        # raw provider payloads -> clean panel
python3 scripts/run_monthly_backtest.py # month-by-month backtest
```

---

## 1. Data

| Series | Instrument | Source |
|---|---|---|
| `gold` | COMEX front-month gold future | Yahoo Finance `GC=F`, daily OHLC |
| `eur` | CME front-month Euro FX future | Yahoo Finance `6E=F`, daily OHLC |
| `aud` | CME front-month Australian Dollar future | Yahoo Finance `6A=F`, daily OHLC |
| `real_yield` | 10-Year TIPS constant-maturity real yield | FRED `DFII10` |

- **123 real trading sessions**, 2026-01-02 → 2026-06-30 (Jan 20, Feb 19, Mar 22, Apr 21, May 20, Jun 21).
- Raw provider payloads are cached verbatim in `data/raw/`; `scripts/build_dataset.py` only reshapes them (epoch → exchange-local session date, arrays → OHLC records, as-of join of the real yield). Nothing is invented or smoothed.
- A session enters the panel only if all three instruments **and** the real yield are genuinely present. The yield join is as-of (most recent publication on or before the session), so FRED holidays never inject future data.
- Validated on load: all 123 sessions in all three instruments satisfy `low ≤ open, close ≤ high`, with no null bars.

**Note on instrument choice.** The previous loader claimed Investing.com spot XAU/USD, EUR/USD and AUD/USD. Yahoo's spot FX feed returns bars where `open ≈ close`, which is degenerate for a strategy whose entire signal is the sign of `close − open`. Exchange-traded futures carry genuine session OHLC, so they are used instead. This is a real difference: the model now trades gold, EUR and AUD *futures*, not spot.

---

## 2. Headline results (tradeable / causal mode)

Each month restarts from $100,000 so months are comparable. The H1 row compounds across the whole window.

| Period | Sessions | Trade days | Return | Day WR | Asset WR | PF | Max DD | Sharpe | Final equity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| January 2026 | 20 | 3 | **+71.81%** | 66.67% | 77.78% | 2.19 | −0.27% | 5.42 | $171,814 |
| February 2026 | 19 | 1 | −23.96% | 0.00% | 33.33% | 0.41 | 0.00% | 0.00 | $76,040 |
| March 2026 | 22 | 1 | −21.53% | 0.00% | 33.33% | 0.24 | −21.53% | −3.46 | $78,470 |
| April 2026 | 21 | 1 | −31.04% | 0.00% | 0.00% | 0.00 | −31.04% | −3.55 | $68,965 |
| May 2026 | 20 | 1 | −24.14% | 0.00% | 0.00% | 0.00 | −24.14% | −3.64 | $75,856 |
| June 2026 | 21 | 2 | −45.72% | 0.00% | 16.67% | 0.02 | −45.72% | −4.14 | $54,279 |
| **2026 H1 (compounded)** | 123 | 4 | **+30.65%** | 50.00% | 66.67% | 1.24 | −23.96% | 1.10 | $130,648 |

**Five of six months lose money.** The single positive month (January) and the positive H1 figure both rest on a handful of trades — 4 trade days in the entire compounded half-year. None of the original goals (day WR > 80%, ROI > 1000%, DD < 20%) are met on real data.

The month rows do not compound to the H1 row: monthly runs reset capital *and* reset the drawdown circuit breaker, so the continuous run halts earlier and takes fewer trades. The H1 row is the one to trust as a portfolio result.

---

## 3. Two engine defects found and fixed

Running the original code on real data surfaced two bugs that were inflating results.

### 3.1 Look-ahead bias in the signal (the big one)

The engine decided whether to trade using session D's **close** (the alignment filter is `close < open` for all three assets), then entered at session D's **open**. The direction traded was therefore the direction the session had *already been observed to move*. Every aligned day was profitable by construction — which is exactly why the original run showed 100% win rates.

Fixed by adding `execution.signal_lag_days` (default **1**): the regime and alignment filter are read from the previous completed session and traded on the next open. Setting it to `0` restores the old same-session behaviour, retained only as a diagnostic.

The look-ahead numbers, for reference — **these are not results, they are an unattainable upper bound**:

| Period | Return (look-ahead) | Day WR |
|---|---:|---:|
| January 2026 | +12.17% | 66.67% |
| February 2026 | −21.05% | 0.00% |
| March 2026 | +13,893.39% | 100.00% |
| April 2026 | +944.05% | 100.00% |
| May 2026 | +481.93% | 100.00% |
| June 2026 | +1,293.16% | 100.00% |

March going from +13,893% to −21.53% once the bias is removed is the entire measure of the problem. Essentially all of the model's apparent edge was look-ahead.

### 3.2 Risk circuit breakers never fired

`check_max_drawdown` and `check_daily_loss_limit` were called, logged `"Halting."` — and then did nothing. The configured 20% max-drawdown and 10% daily-loss limits had no effect. In the first causal run this let February compound down to −92.94% and the H1 run to −99.98%.

Fixed with a `halted` flag that actually blocks new entries once tripped. With breakers live, worst month is −45.72% instead of −92.94%.

---

## 4. Honest read

- The strategy is **not validated** on real Jan–Jun 2026 data. Its published performance was an artefact of look-ahead bias plus inoperative risk limits.
- The sample is tiny: 4 trade days across 123 sessions in the compounded run. Nothing here is statistically meaningful in either direction, and the positive H1 return should not be read as an edge.
- 500x leverage with 20% of equity at risk means a 1% adverse move costs ~33% of equity on a three-asset day. Single-trade losses of exactly −1.00% price move (`STOP_LOSS`) map to catastrophic equity moves. The sizing is not survivable as configured.
- Costs are still zero — `commission_per_trade: 0.0`, `slippage_pct: 0.0`. Real execution at this leverage and turnover would make the results materially worse.

---

## 5. Artefacts

```
data/raw/                      raw provider payloads, cached verbatim
data/market_data_2026.json     clean 123-session panel
backtest_results/2026/
  monthly_summary.csv/.json    per-month + H1 metrics, both modes
  trades_2026-01..06.csv       per-month trade blotters
  equity_2026-01..06.csv       per-month daily equity curves
  trades_2026H1.csv            compounded run blotter
  equity_2026H1.csv            compounded run equity curve
```
