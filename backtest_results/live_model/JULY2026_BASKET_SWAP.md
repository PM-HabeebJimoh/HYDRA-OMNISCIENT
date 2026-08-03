# AGBA METTA MODEL — Basket Substitution Backtest, July 2026

Universe XAUUSD/EURUSD/AUDUSD removed and replaced by each candidate basket.
Everything else is the model exactly as `src/engine.py` implements it:

```
Regime      real yield > 0.7   = CONTRACTION -> SHORT
            real yield < -0.1  = EXPANSION   -> LONG
            otherwise          = STABILITY   -> no trade
Alignment   CONTRACTION requires ALL assets close < open
            EXPANSION   requires ALL assets close > open
            misaligned  = SKIP the day
Entry       that day's OPEN          (entry_date == exit_date)
Exit        that day's CLOSE, unless the 1% hard stop is hit intraday
Sizing      risk_per_trade_pct 0.20, equal weight across 3 assets, 500x leverage
```

Metrics are the model's own: trade_days, day/asset win rate, profit_factor,
max_drawdown_pct, sharpe_ratio, and the GOAL CHECK from `main.py`.

---

## COMPARISON — JULY 2026

| universe | trade_days | day_WR | asset_WR | return | maxDD | sharpe |
|---|---:|---:|---:|---:|---:|---:|
| **XAUUSD+EURUSD+AUDUSD** | 6 | 100.0% | 100.0% | **+1796.05%** | 0.00% | 8.47 |
| AUDUSD+GBPUSD+USDCAD | 5 | 100.0% | 100.0% | +157.75% | 0.00% | **8.57** |
| EURUSD+AUDUSD+USDCAD | 4 | 100.0% | 100.0% | +108.59% | 0.00% | 7.60 |
| GBPUSD+NZDUSD+USDCAD | 3 | 100.0% | 100.0% | +104.70% | 0.00% | 6.03 |
| NZDUSD+USDCAD+USDJPY | 1 | 100.0% | 100.0% | +15.05% | 0.00% | 3.64 |

**The original XAU/EUR/AUD basket WINS on return by a wide margin.** None of the
four substitutes comes close. Only AUDUSD+GBPUSD+USDCAD edges it on Sharpe (8.57
vs 8.47), and that is on 5 trade days versus 6.

GOAL CHECK (model's thresholds: day WR > 80%, ROI > 1000%, DD < 20%):

| universe | Day WR | ROI | DD | OVERALL |
|---|---|---|---|---|
| XAUUSD+EURUSD+AUDUSD | PASS | **PASS** | PASS | **ALL GOALS MET** |
| AUDUSD+GBPUSD+USDCAD | PASS | FAIL (157.8%) | PASS | not achieved |
| EURUSD+AUDUSD+USDCAD | PASS | FAIL (108.6%) | PASS | not achieved |
| GBPUSD+NZDUSD+USDCAD | PASS | FAIL (104.7%) | PASS | not achieved |
| NZDUSD+USDCAD+USDJPY | PASS | FAIL (15.0%) | PASS | not achieved |

## Why the original basket wins

Gold. Look at the per-trade `pnl_pct` column in `july2026_basket_swap.json`:

    XAUUSD moves 1.4320%, 2.9299%, 2.1154%, 2.0223% per trade day
    USDCAD moves 0.0211%, 0.0212%, 0.1495%, 0.0213%

At 500x, XAUUSD's ~2% daily range is the entire engine. USDCAD contributes
almost nothing — it is the quietest instrument of the ten (mean daily move
0.2064%). Every basket that swapped gold out for USDCAD traded a much smaller
range and returned proportionally less.

That is also why my earlier "AUDUSD+GBPUSD+USDCAD is better" ranking was wrong
for this model: I ranked baskets by t-statistic, which measures consistency per
unit of volatility. **This model is not sized by volatility — it applies a flat
500x to everything, so raw range is what produces return.** Ranking by t-stat
picked the calmest basket, which is the worst possible choice here.

## The critical mechanic, stated plainly

`entry_date == exit_date` in every trade record, in the author's original run and
in these. The model:

1. reads the **close** of day D to test alignment, then
2. enters at the **open** of day D — a price that occurred *before* the close it
   just used.

Alignment is confirmed by information that does not exist at entry time. That is
why day win rate is 100% and max drawdown is 0.00% in every single run above,
including all four substitutes. The model only ever enters on days it has already
confirmed closed in its favour.

This is not a criticism of the basket choice — it applies identically to all five
universes, which is why all five show a perfect win rate. It is the reason the
+1796.05% is not attainable in live trading.

## Data note

The 7 non-core pairs in `data/raw/xpairs/` carry open/close only, no high/low, so
`Stop evaluable: False` for the four substitute baskets. No stop was ever hit in
any run (all exits are `CLOSE`), so this does not change these particular
numbers — but the substitutes are running without stop protection.

## Result

Answering the question asked: **all four substitute baskets were backtested for
July 2026 under the full Agba Metta model, and all four underperform the original
XAUUSD/EURUSD/AUDUSD universe.** The original is the best of the five, and the
only one that meets the model's ROI goal.

Files: `backtest_results/live_model/july2026_basket_swap.json` (full trade
records), reproduce with `python3 -m research.agba_swap_july`
