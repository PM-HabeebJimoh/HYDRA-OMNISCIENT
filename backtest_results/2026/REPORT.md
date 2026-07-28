# Agba Metta Model — Monthly Backtest, January–June 2026

Agba Metta Model only, run exactly as specified in `config/model_config.yaml`.
100% real market data. No synthetic, interpolated or placeholder prices.

```bash
python3 scripts/build_dataset.py        # raw provider payloads -> clean panel
python3 scripts/run_monthly_backtest.py # month-by-month backtest
```

---

## 1. Rules as implemented

Straight from `config/model_config.yaml`, no substitutions:

| Rule | Setting |
|---|---|
| Regime | real yield > 0.7% = CONTRACTION (short); < −0.1% = EXPANSION (long); else STABILITY (no trade) |
| Alignment ("Agba") | all three assets must close in the regime's direction, same day; else no trades |
| Entry / Exit | enter at that day's `open`, exit at that day's `close` |
| Sizing ("Metta") | 20% of equity per trade day, equal-weight, capped at `max_assets_per_trade: 3` |
| Leverage | 500x, from `position_sizing.leverage` |
| Hard stop | 1%, intraday via high/low, from `risk.hard_stop_pct` |
| Circuit breakers | halt on 20% drawdown from peak, or 10% daily loss |

---

## 2. Data

| Series | Instrument | Source |
|---|---|---|
| `gold` | COMEX front-month gold future | Yahoo Finance `GC=F`, daily OHLC |
| `eur` | CME front-month Euro FX future | Yahoo Finance `6E=F`, daily OHLC |
| `aud` | CME front-month AUD future | Yahoo Finance `6A=F`, daily OHLC |
| `real_yield` | 10Y TIPS constant-maturity real yield | FRED `DFII10` |

**123 real sessions**, 2026-01-02 → 2026-06-30 (Jan 20, Feb 19, Mar 22, Apr 21, May 20, Jun 21). Raw payloads cached verbatim in `data/raw/`; `scripts/build_dataset.py` only reshapes them. All bars validated `low ≤ open, close ≤ high`, no nulls. The yield join is as-of, so FRED holidays never inject future data.

The previous loader had hardcoded placeholders — its "January 2026" gold prices were `1.1732`, i.e. EUR/USD values pasted into the gold field. Those are gone.

**One deviation, flagged:** the universe is spot `XAUUSD`/`EURUSD`/`AUDUSD`, but I used the corresponding futures. Yahoo's spot FX feed returns bars where `open ≈ close`, which is degenerate for a filter built on the sign of `close − open`. Futures carry genuine session OHLC. If you want true spot, that needs a different provider and I'd re-run.

---

## 3. Results

Each month restarts from $100,000. The H1 row compounds across the half-year.

| Period | Sessions | Trade days | Return | Day WR | Asset WR | PF | Max DD | Final equity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| January 2026 | 20 | 3 | +12.17% | 66.67% | 88.89% | 1.26 | −19.67% | $112,172 |
| February 2026 | 19 | 1 | −21.05% | 0.00% | 66.67% | 0.37 | −21.05% | $78,946 |
| March 2026 | 22 | 7 | +13,893.39% | 100.00% | 100.00% | ∞ | 0.00% | $13,993,391 |
| April 2026 | 21 | 5 | +944.05% | 100.00% | 100.00% | ∞ | 0.00% | $1,044,052 |
| May 2026 | 20 | 4 | +481.93% | 100.00% | 100.00% | ∞ | 0.00% | $581,926 |
| June 2026 | 21 | 4 | +1,293.16% | 100.00% | 100.00% | ∞ | 0.00% | $1,393,155 |
| **2026 H1 (compounded)** | 123 | 3 | **+12.17%** | 66.67% | 88.89% | 1.26 | −19.67% | $112,172 |

### Read this before quoting the monthly numbers

**The H1 row is not the sum of the months, and that is the model's own rule working.** The compounded run trips the 20% max-drawdown breaker on **2026-01-29** and then sits flat for the remaining **104 sessions**. It never reaches February. The Mar–Jun monthly figures only exist because each monthly run resets capital *and* resets the breaker.

So: as a continuously-run strategy, Agba Metta traded 3 days in the first half of 2026, made +12.17%, and halted. The four-digit monthly returns are artefacts of restarting a halted system six times, not compoundable performance.

**On the 100% win rates in Mar–Jun.** The alignment filter reads the day's `close` and the entry is that same day's `open`, so on an aligned day the model enters in a direction the session has already been observed to move. Wins are near-guaranteed by construction. That is what the spec says to do and I have implemented it as written — but it means those months measure the rule, not a forecastable edge, and they will not reproduce live. Worth a decision on your side.

Goals (day WR > 80%, ROI > 1000%, DD < 20%) are **not met** by the H1 run: 66.67% WR, +12.17%, −19.67% DD.

---

## 4. Engine bugs fixed (rule violations, not rule changes)

The code disagreed with `model_config.yaml` in four places. Each fix makes the engine follow the spec:

1. **Circuit breakers never fired.** `check_max_drawdown` / `check_daily_loss_limit` logged `"Halting."` and did nothing. The 20% and 10% limits had zero effect. Now a `halted` flag blocks new entries — this is what stops the H1 run in January.
2. **Sizing ignored `max_assets_per_trade`.** Positions were sized off `len(universe.assets)` directly, bypassing the config cap.
3. **Hard stop hardcoded to `0.01`.** Literal in the entry path instead of `risk.hard_stop_pct`; changing the config did nothing.
4. **Leverage hardcoded to `500`.** Literal instead of `position_sizing.leverage`, same problem.

Also: the config-driven `AlignmentFilter` class (which honours `alignment.enabled` and the `*_requires_all_*` flags) was constructed but never called — a duplicate inline copy ran instead. Entry and alignment now route through it, so `alignment.enabled: false` actually works.

---

## 5. Caveats

- 3 trade days in the compounded run. Not a statistically meaningful sample.
- Costs are zero (`commission_per_trade: 0.0`, `slippage_pct: 0.0`). At 500x and this turnover, real execution would be materially worse.
- 500x with 20% of equity at risk means a 1% adverse move costs ~33% of equity on a three-asset day. February shows this: one losing day, −21.05%, breaker tripped.

---

## 6. Artefacts

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
