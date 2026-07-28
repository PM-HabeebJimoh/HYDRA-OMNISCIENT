#!/usr/bin/env python3
"""
HYDRA-S3-MAX | FULL REAL BACKTEST — JULY 2026
==============================================
Focused re-run of the `hydra-s3-max-actual-system` methodology over July 2026
on real market data only, honouring the OHLC of every entry candle and the
1% hard stop against the candle's intraday extreme.

System configuration is taken from the live code, not invented here:
    config.py  THRESHOLDS['CONTRACTION_YIELD'] = 0.7
    config.py  THRESHOLDS['EXPANSION_YIELD']   = -0.1
    config.py  THRESHOLDS['HARD_STOP_PCT']     = 0.01
    actual-system: 20% of equity per trade day, 500x leverage, split evenly
                   across XAUUSD / EURUSD / AUDUSD, all-3 alignment filter.

Data (real, no simulation)
--------------------------
    XAUUSD  GC=F COMEX gold futures daily OHLC  — Yahoo Finance v8 chart API
    EURUSD  EURUSD=X spot daily OHLC            — Yahoo Finance v8 chart API
    AUDUSD  AUDUSD=X spot daily OHLC            — Yahoo Finance v8 chart API
    yield   DFII10 10y TIPS constant maturity   — FRED
Raw payloads archived verbatim in data/raw/*_2026-07.json.

Modes (identical to the H1 run so the two are directly comparable)
------------------------------------------------------------------
`as_published`   reproduces the July script on this branch: the alignment
                 filter reads the SAME candle the trade is entered on
                 (close < open) while entering at that candle's open and
                 exiting at that candle's close. The return is then
                 (open-close)/open, which is positive whenever the filter
                 passes — profit is an identity, not a forecast.

`point_in_time`  the same system made causally honest: alignment read from the
                 last COMPLETED session, regime from the last real-yield print
                 available before the open, entry at the next session's open.

Entry-candle pricing is identical in both modes:
    entry        = session open
    stop (SHORT) = entry * 1.01
    high >= stop -> filled at the stop (loss booked)
    else         -> exited at the session close
Where a candle both breaches the stop and closes profitably, the stop is
assumed to trigger first: daily bars do not reveal the intraday path, so the
conservative assumption is used.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from backtest_actual_system_2026H1 import (
    ASSETS,
    CONTRACTION_YIELD,
    EXPANSION_YIELD,
    HARD_STOP_PCT,
    INITIAL_CAPITAL,
    LEVERAGE,
    RISK_PER_DAY,
    build_sessions,
    metrics,
    run,
)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(ROOT, "backtest_results")

JULY_START, JULY_END = "2026-07-01", "2026-07-31"


def weekly_table(days) -> pd.DataFrame:
    rows = []
    for d in days:
        iso = pd.Timestamp(d.date).isocalendar()
        rows.append({"week": f"{iso.year}-W{iso.week:02d}", "rec": d})
    out = []
    for wk in sorted({r["week"] for r in rows}):
        wd = [r["rec"] for r in rows if r["week"] == wk]
        td = [d for d in wd if d.traded]
        tr = [t for d in wd for t in d.trades]
        start_eq, end_eq = wd[0].equity_open, wd[-1].equity_close
        eq = pd.Series([start_eq] + [d.equity_close for d in wd], dtype=float)
        dd = ((eq - eq.cummax()) / eq.cummax()).min() * 100
        out.append({
            "week": wk,
            "dates": f"{wd[0].date}..{wd[-1].date}",
            "sessions": len(wd),
            "trade_days": len(td),
            "trades": len(tr),
            "wins": sum(1 for d in td if d.pnl > 0),
            "stop_hits": sum(1 for t in tr if t.stop_hit),
            "equity_start": round(start_eq, 2),
            "equity_end": round(end_eq, 2),
            "pnl": round(end_eq - start_eq, 2),
            "return_pct": round((end_eq / start_eq - 1) * 100, 2) if start_eq > 0 else 0.0,
            "max_dd_pct": round(float(dd), 2),
        })
    return pd.DataFrame(out)


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    px = pd.read_csv(os.path.join(DATA, "ohlc_daily_2026H1.csv"))
    ry = pd.read_csv(os.path.join(DATA, "real_yield_daily_2026H1.csv"))
    wide = build_sessions(px)

    july_sessions = [d for d in wide.index if JULY_START <= d <= JULY_END]
    print("=" * 78)
    print("HYDRA-S3-MAX | JULY 2026 FULL REAL BACKTEST")
    print("=" * 78)
    print(f"Complete sessions (all 3 assets have a real bar): {len(july_sessions)}")
    print(f"  {july_sessions[0]} .. {july_sessions[-1]}")
    print(f"Config: {HARD_STOP_PCT:.0%} hard stop | {RISK_PER_DAY:.0%} risk/day | "
          f"{LEVERAGE}x leverage | {len(ASSETS)} assets")
    print(f"Notional per asset = {RISK_PER_DAY * LEVERAGE / len(ASSETS):.1f}x equity | "
          f"one stop-out costs {RISK_PER_DAY * LEVERAGE / len(ASSETS) * HARD_STOP_PCT:.1%} of equity")

    out = {}
    for mode in ("as_published", "point_in_time"):
        days, trades = run(mode, wide, ry, start=JULY_START, end=JULY_END)
        m = metrics(days, trades)
        wt = weekly_table(days)
        out[mode] = {"metrics": m, "weekly": wt, "days": days, "trades": trades}

        print("\n" + "=" * 78)
        print(f"MODE: {mode}")
        print("=" * 78)
        print(wt.to_string(index=False))
        print(f"\n  Final equity      ${m['final_equity']:,.2f}")
        print(f"  Total return      {m['total_return_pct']:+,.2f}%")
        print(f"  Trade days        {m['trade_days']} of {m['sessions_evaluated']} sessions")
        print(f"  Day win rate      {m['day_win_rate_pct']:.2f}%  ({m['day_wins']}W / {m['day_losses']}L)")
        print(f"  Asset trades      {m['asset_trades']}  win rate {m['asset_win_rate_pct']:.2f}%")
        print(f"  Stop-loss hits    {m['stop_loss_hits']}")
        print(f"  Profit factor     {m['profit_factor']}")
        print(f"  Max drawdown      {m['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe            {m['sharpe_ratio']}")

        print("\n  Trade-by-trade (real OHLC, 1% hard stop):")
        for t in trades:
            print(f"    {t.date} {t.asset:7s} {t.direction:5s} "
                  f"entry {t.entry:>10.5f} stop {t.stop:>10.5f} "
                  f"H {t.high:>10.5f} L {t.low:>10.5f} C {t.close:>10.5f} "
                  f"exit {t.exit:>10.5f} {t.ret * 100:+7.3f}% "
                  f"${t.pnl:>14,.2f} {t.exit_reason}")

        pd.DataFrame([{
            "date": t.date, "asset": t.asset, "direction": t.direction,
            "entry": t.entry, "stop": t.stop, "exit": t.exit,
            "high": t.high, "low": t.low, "close": t.close,
            "return_pct": t.ret * 100, "pnl_usd": t.pnl,
            "exit_reason": t.exit_reason, "stop_hit": t.stop_hit,
            "notional_usd": t.notional,
        } for t in trades]).to_csv(os.path.join(RESULTS, f"trades_july2026_{mode}.csv"), index=False)

        pd.DataFrame([{
            "date": d.date, "regime": d.regime, "real_yield": d.yield_val,
            "yield_asof": d.yield_asof, "signal_from": d.signal_date,
            "aligned": d.aligned, "traded": d.traded, "reason": d.reason,
            "equity_open": d.equity_open, "equity_close": d.equity_close, "pnl": d.pnl,
        } for d in days]).to_csv(os.path.join(RESULTS, f"daily_july2026_{mode}.csv"), index=False)

        wt.to_csv(os.path.join(RESULTS, f"weekly_july2026_{mode}.csv"), index=False)

    with open(os.path.join(RESULTS, "summary_july2026.json"), "w") as fh:
        json.dump({
            "model": "HYDRA-S3-MAX",
            "branch": "hydra-s3-max-actual-system",
            "period": f"{JULY_START} .. {july_sessions[-1]} (last completed session)",
            "today": "2026-07-28",
            "data_sources": {
                "XAUUSD": "Yahoo Finance v8 chart API — GC=F COMEX gold futures daily OHLC",
                "EURUSD": "Yahoo Finance v8 chart API — EURUSD=X spot daily OHLC",
                "AUDUSD": "Yahoo Finance v8 chart API — AUDUSD=X spot daily OHLC",
                "real_yield": "FRED DFII10 — 10y TIPS constant maturity",
            },
            "system_config": {
                "contraction_yield_pct": CONTRACTION_YIELD,
                "expansion_yield_pct": EXPANSION_YIELD,
                "hard_stop_pct": HARD_STOP_PCT,
                "risk_per_day": RISK_PER_DAY,
                "leverage": LEVERAGE,
                "assets": ASSETS,
                "notional_per_asset_x_equity": round(RISK_PER_DAY * LEVERAGE / 3, 2),
                "equity_loss_if_one_asset_stops_out_pct": round(
                    RISK_PER_DAY * LEVERAGE / 3 * HARD_STOP_PCT * 100, 2),
            },
            "sessions": july_sessions,
            "modes": {k: v["metrics"] for k, v in out.items()},
            "weekly": {k: v["weekly"].to_dict(orient="records") for k, v in out.items()},
        }, fh, indent=2)

    print(f"\nResults written to {RESULTS}/")


if __name__ == "__main__":
    main()
