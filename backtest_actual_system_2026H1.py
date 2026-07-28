#!/usr/bin/env python3
"""
HYDRA-S3-MAX | FULL REAL BACKTEST — JANUARY 2026 → JUNE 2026
=============================================================
Re-runs the `hydra-s3-max-actual-system` methodology month by month on real
market data only, honouring the OHLC of every entry candle and the hard stop.

System configuration is taken from the live code, not invented here:
    config.py     THRESHOLDS['CONTRACTION_YIELD'] = 0.7   (TIPS 10y > 0.7% -> CONTRACTION)
    config.py     THRESHOLDS['EXPANSION_YIELD']   = -0.1
    config.py     THRESHOLDS['HARD_STOP_PCT']     = 0.01  (1% hard stop)
    actual-system 20% of equity risked per trade day, 500x leverage,
                  split evenly across the 3 traded assets, alignment filter.

Data (real, no simulation)
--------------------------
    XAUUSD  COMEX gold futures GC=F daily OHLC   — Yahoo Finance v8 chart API
    EURUSD  EUR/USD spot daily OHLC              — Yahoo Finance v8 chart API
    AUDUSD  AUD/USD spot daily OHLC              — Yahoo Finance v8 chart API
    Real yield  DFII10 10y TIPS constant maturity — FRED
Raw payloads are archived verbatim in data/raw/, normalised by
build_market_data.py into data/ohlc_daily_2026H1.csv.

Two execution modes are reported
--------------------------------
`as_published`  reproduces the July script on this branch exactly: the
                alignment filter reads the SAME candle the trade is entered on
                (close < open) while entering at that candle's open. Because
                the exit is that same close, the trade is profitable by
                construction — the filter cannot be evaluated without already
                knowing the outcome. Kept only for continuity with the
                published July numbers.

`point_in_time` the same system made causally honest: the alignment signal is
                read from the LAST COMPLETED session, the regime from the last
                real-yield print available before the open, and the trade is
                then entered at the next session's open. Nothing that happens
                after the entry decision is used to make it. This is the number
                that actually describes the strategy's edge.

Both modes price the entry candle identically and honestly:
    entry            = session open
    stop (SHORT)     = entry * (1 + 0.01)
    if session high >= stop   -> filled at the stop, loss booked
    else                      -> exited at the session close
When a candle both stops out and would otherwise have been profitable, the
stop is assumed to trigger first (the conservative assumption, since daily
bars do not reveal the intraday path).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(ROOT, "backtest_results")

# ── ACTUAL SYSTEM CONFIG (mirrors config.py / live_engine.py) ────────────────
CONTRACTION_YIELD = 0.7
EXPANSION_YIELD = -0.1
HARD_STOP_PCT = 0.01
RISK_PER_DAY = 0.20
LEVERAGE = 500
INITIAL_CAPITAL = 100_000.0
ASSETS = ["XAUUSD", "EURUSD", "AUDUSD"]

START, END = "2026-01-01", "2026-06-30"


def regime_for(yield_val: float) -> str:
    if yield_val > CONTRACTION_YIELD:
        return "CONTRACTION"
    if yield_val < EXPANSION_YIELD:
        return "EXPANSION"
    return "STABILITY"


@dataclass
class Trade:
    date: str
    asset: str
    direction: str
    entry: float
    stop: float
    exit: float
    high: float
    low: float
    close: float
    ret: float
    pnl: float
    exit_reason: str
    stop_hit: bool
    notional: float


@dataclass
class DayRecord:
    date: str
    regime: str
    yield_val: float
    yield_asof: str
    signal_date: str
    aligned: bool
    traded: bool
    reason: str
    equity_open: float
    equity_close: float
    pnl: float = 0.0
    trades: list = field(default_factory=list)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    px = pd.read_csv(os.path.join(DATA, "ohlc_daily_2026H1.csv"))
    ry = pd.read_csv(os.path.join(DATA, "real_yield_daily_2026H1.csv"))
    return px, ry


def build_sessions(px: pd.DataFrame) -> pd.DataFrame:
    """Wide frame: one row per session that has a real bar for all 3 assets."""
    frames = []
    for asset in ASSETS:
        a = px[px["asset"] == asset].set_index("date")[["open", "high", "low", "close"]]
        a.columns = pd.MultiIndex.from_product([[asset], a.columns])
        frames.append(a)
    wide = pd.concat(frames, axis=1).sort_index()
    wide = wide.dropna()  # a session must have all three real bars
    return wide


def run(mode: str, wide: pd.DataFrame, ry: pd.DataFrame,
        start: str = START, end: str = END) -> tuple[list[DayRecord], list[Trade]]:
    """mode: 'as_published' | 'point_in_time'"""
    yields = ry.set_index("date")["real_yield"].sort_index()
    y_dates = list(yields.index)
    y_vals = list(yields.values)

    # Evaluate only inside [start, end], but keep the full session list so the
    # point-in-time signal for the first evaluated day can legitimately come
    # from the last completed session *before* the window opens.
    all_sessions = list(wide.index)
    sessions = [d for d in all_sessions if start <= d <= end]
    equity = INITIAL_CAPITAL
    days: list[DayRecord] = []
    trades: list[Trade] = []

    for date in sessions:
        i = all_sessions.index(date)
        row = wide.loc[date]

        # ── regime input ────────────────────────────────────────────────────
        if mode == "as_published":
            # same-day yield print (as the July script did)
            idx = np.searchsorted(y_dates, date, side="right") - 1
        else:
            # strictly the last print available BEFORE this session opens
            idx = np.searchsorted(y_dates, date, side="left") - 1
        if idx < 0:
            days.append(DayRecord(date, "NO_DATA", float("nan"), "-", "-", False, False,
                                  "no real-yield print available yet", equity, equity))
            continue
        yv, yasof = float(y_vals[idx]), y_dates[idx]
        regime = regime_for(yv)

        # ── alignment signal ────────────────────────────────────────────────
        if mode == "as_published":
            sig_date = date  # LOOKAHEAD: reads the candle it trades
        else:
            if i == 0:
                days.append(DayRecord(date, regime, yv, yasof, "-", False, False,
                                      "no prior session for signal", equity, equity))
                continue
            sig_date = all_sessions[i - 1]
        sig = wide.loc[sig_date]

        down = {a: sig[(a, "close")] < sig[(a, "open")] for a in ASSETS}
        up = {a: sig[(a, "close")] > sig[(a, "open")] for a in ASSETS}

        if regime == "CONTRACTION":
            aligned, direction = all(down.values()), "SHORT"
        elif regime == "EXPANSION":
            aligned, direction = all(up.values()), "LONG"
        else:
            aligned, direction = False, "NONE"

        if equity <= 0:
            days.append(DayRecord(date, regime, yv, yasof, sig_date, aligned, False,
                                  "account wiped out — no capital left", equity, equity))
            continue

        if not aligned:
            miss = [a for a in ASSETS if not (down[a] if regime == "CONTRACTION" else up[a])]
            reason = (f"{regime}: alignment failed on {', '.join(miss)}"
                      if regime != "STABILITY" else "STABILITY regime — system flat")
            days.append(DayRecord(date, regime, yv, yasof, sig_date, aligned, False,
                                  reason, equity, equity))
            continue

        # ── execute: 20% of equity, 500x, split across the 3 assets ─────────
        notional_per_asset = equity * RISK_PER_DAY * LEVERAGE / len(ASSETS)
        day_pnl, day_trades = 0.0, []

        for asset in ASSETS:
            o = float(row[(asset, "open")])
            h = float(row[(asset, "high")])
            l = float(row[(asset, "low")])
            c = float(row[(asset, "close")])

            if direction == "SHORT":
                stop = o * (1 + HARD_STOP_PCT)
                stop_hit = h >= stop
                exit_px = stop if stop_hit else c
                ret = (o - exit_px) / o
            else:
                stop = o * (1 - HARD_STOP_PCT)
                stop_hit = l <= stop
                exit_px = stop if stop_hit else c
                ret = (exit_px - o) / o

            pnl = notional_per_asset * ret
            day_pnl += pnl
            t = Trade(date, asset, direction, o, stop, exit_px, h, l, c, ret, pnl,
                      "STOP_LOSS" if stop_hit else "CLOSE", stop_hit, notional_per_asset)
            day_trades.append(t)
            trades.append(t)

        eq_open = equity
        equity = max(0.0, equity + day_pnl)
        days.append(DayRecord(date, regime, yv, yasof, sig_date, True, True,
                              f"{regime} + all-3 aligned -> {direction}",
                              eq_open, equity, day_pnl, day_trades))

    return days, trades


def metrics(days: list[DayRecord], trades: list[Trade]) -> dict:
    eq = [INITIAL_CAPITAL] + [d.equity_close for d in days]
    eq = pd.Series(eq, dtype=float)
    peak = eq.cummax()
    dd = (eq - peak) / peak
    trade_days = [d for d in days if d.traded]
    wins = [d for d in trade_days if d.pnl > 0]
    gp = sum(t.pnl for t in trades if t.pnl > 0)
    gl = abs(sum(t.pnl for t in trades if t.pnl < 0))
    rets = eq.pct_change().dropna().replace([np.inf, -np.inf], np.nan).dropna()

    return {
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(float(eq.iloc[-1]), 2),
        "total_return_pct": round((float(eq.iloc[-1]) / INITIAL_CAPITAL - 1) * 100, 2),
        "sessions_evaluated": len(days),
        "trade_days": len(trade_days),
        "day_wins": len(wins),
        "day_losses": len(trade_days) - len(wins),
        "day_win_rate_pct": round(len(wins) / len(trade_days) * 100, 2) if trade_days else 0.0,
        "asset_trades": len(trades),
        "asset_wins": sum(1 for t in trades if t.pnl > 0),
        "asset_win_rate_pct": round(sum(1 for t in trades if t.pnl > 0) / len(trades) * 100, 2) if trades else 0.0,
        "stop_loss_hits": sum(1 for t in trades if t.stop_hit),
        "profit_factor": round(gp / gl, 3) if gl > 0 else ("inf" if gp > 0 else 0.0),
        "max_drawdown_pct": round(float(dd.min()) * 100, 2),
        "sharpe_ratio": round(float(rets.mean() / rets.std() * np.sqrt(252)), 2) if len(rets) > 1 and rets.std() else 0.0,
        "ruin": bool(float(eq.iloc[-1]) <= 0.0),
    }


def monthly_table(days: list[DayRecord]) -> pd.DataFrame:
    rows = []
    for m in ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]:
        md = [d for d in days if d.date.startswith(m)]
        if not md:
            rows.append({"month": m, "sessions": 0, "trade_days": 0, "trades": 0,
                         "wins": 0, "win_rate_pct": 0.0, "stop_hits": 0,
                         "equity_start": np.nan, "equity_end": np.nan,
                         "pnl": 0.0, "return_pct": 0.0, "max_dd_pct": 0.0})
            continue
        td = [d for d in md if d.traded]
        tr = [t for d in md for t in d.trades]
        start_eq = md[0].equity_open
        end_eq = md[-1].equity_close
        eq = pd.Series([start_eq] + [d.equity_close for d in md], dtype=float)
        peak = eq.cummax()
        dd = ((eq - peak) / peak).min() * 100
        rows.append({
            "month": m,
            "sessions": len(md),
            "trade_days": len(td),
            "trades": len(tr),
            "wins": sum(1 for d in td if d.pnl > 0),
            "win_rate_pct": round(sum(1 for d in td if d.pnl > 0) / len(td) * 100, 2) if td else 0.0,
            "stop_hits": sum(1 for t in tr if t.stop_hit),
            "equity_start": round(start_eq, 2),
            "equity_end": round(end_eq, 2),
            "pnl": round(end_eq - start_eq, 2),
            "return_pct": round((end_eq / start_eq - 1) * 100, 2) if start_eq > 0 else 0.0,
            "max_dd_pct": round(float(dd), 2),
        })
    return pd.DataFrame(rows)


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    px, ry = load_data()
    wide = build_sessions(px)

    out = {}
    for mode in ("as_published", "point_in_time"):
        days, trades = run(mode, wide, ry)
        m = metrics(days, trades)
        mt = monthly_table(days)
        out[mode] = {"metrics": m, "monthly": mt, "days": days, "trades": trades}

        print("\n" + "=" * 78)
        print(f"MODE: {mode}")
        print("=" * 78)
        print(mt.to_string(index=False))
        print(f"\n  Final equity      ${m['final_equity']:,.2f}")
        print(f"  Total return      {m['total_return_pct']:+,.2f}%")
        print(f"  Trade days        {m['trade_days']} of {m['sessions_evaluated']} sessions")
        print(f"  Day win rate      {m['day_win_rate_pct']:.2f}%  ({m['day_wins']}W / {m['day_losses']}L)")
        print(f"  Asset trades      {m['asset_trades']}  win rate {m['asset_win_rate_pct']:.2f}%")
        print(f"  Stop-loss hits    {m['stop_loss_hits']}")
        print(f"  Profit factor     {m['profit_factor']}")
        print(f"  Max drawdown      {m['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe            {m['sharpe_ratio']}")
        if m["ruin"]:
            print("  *** ACCOUNT WIPED OUT ***")

        # persist
        pd.DataFrame([{
            "date": t.date, "asset": t.asset, "direction": t.direction,
            "entry": t.entry, "stop": t.stop, "exit": t.exit,
            "high": t.high, "low": t.low, "close": t.close,
            "return_pct": t.ret * 100, "pnl_usd": t.pnl,
            "exit_reason": t.exit_reason, "stop_hit": t.stop_hit,
            "notional_usd": t.notional,
        } for t in trades]).to_csv(os.path.join(RESULTS, f"trades_2026H1_{mode}.csv"), index=False)

        pd.DataFrame([{
            "date": d.date, "regime": d.regime, "real_yield": d.yield_val,
            "yield_asof": d.yield_asof, "signal_from": d.signal_date,
            "aligned": d.aligned, "traded": d.traded, "reason": d.reason,
            "equity_open": d.equity_open, "equity_close": d.equity_close, "pnl": d.pnl,
        } for d in days]).to_csv(os.path.join(RESULTS, f"daily_2026H1_{mode}.csv"), index=False)

        mt.to_csv(os.path.join(RESULTS, f"monthly_2026H1_{mode}.csv"), index=False)

    with open(os.path.join(RESULTS, "summary_2026H1.json"), "w") as fh:
        json.dump({
            "model": "HYDRA-S3-MAX",
            "branch": "hydra-s3-max-actual-system",
            "period": f"{START} .. {END}",
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
                "equity_loss_if_one_asset_stops_out_pct": round(RISK_PER_DAY * LEVERAGE / 3 * HARD_STOP_PCT * 100, 2),
            },
            "modes": {k: v["metrics"] for k, v in out.items()},
            "monthly": {k: v["monthly"].to_dict(orient="records") for k, v in out.items()},
        }, fh, indent=2)

    print(f"\nResults written to {RESULTS}/")


if __name__ == "__main__":
    main()
