#!/usr/bin/env python3
"""
Run the Agba Metta Model month by month across January - June 2026 on 100%
real market data (see scripts/build_dataset.py for provenance).

Each month is backtested independently from the configured initial capital so
the months are directly comparable, and a continuous compounded run over the
whole half-year is produced alongside them.

Outputs land in backtest_results/2026/:
  monthly_summary.csv / .json   one row per month + the continuous run
  trades_<month>.csv            per-month trade blotter
  equity_<month>.csv            per-month daily equity curve
  trades_2026H1.csv             continuous run blotter
  equity_2026H1.csv             continuous run equity curve
"""

from __future__ import annotations

import json
import sys
from calendar import monthrange
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config_loader import load_config
from src.data_loader import load_market_data_for_backtest
from src.engine import run_backtest

OUT_DIR = ROOT / "backtest_results" / "2026"

MONTHS = [
    ("2026-01", "January 2026"),
    ("2026-02", "February 2026"),
    ("2026-03", "March 2026"),
    ("2026-04", "April 2026"),
    ("2026-05", "May 2026"),
    ("2026-06", "June 2026"),
]


def month_bounds(ym: str) -> tuple[str, str]:
    year, month = (int(x) for x in ym.split("-"))
    return f"{ym}-01", f"{ym}-{monthrange(year, month)[1]:02d}"


def run_window(config, label: str, start: str, end: str, tag: str,
               persist: bool = True) -> dict:
    """Backtest one date window and persist its artefacts."""
    data = load_market_data_for_backtest(start, end)
    if not data:
        print(f"  {label}: no real sessions in window - skipped")
        return {}

    # The engine reads the window off the config object.
    config.backtest.start_date = start
    config.backtest.end_date = end

    trades, equity_curve, metrics = run_backtest(config, data)

    sessions = [d for d in sorted(data) if start <= d <= end]
    row = {
        "period": label,
        "start": sessions[0],
        "end": sessions[-1],
        "sessions": len(sessions),
        "initial_capital": config.backtest.initial_capital,
        "final_equity": metrics.get("final_equity", config.backtest.initial_capital),
        "total_return_pct": metrics.get("total_return_pct", 0.0),
        "trade_days": metrics.get("trade_days", 0),
        "day_wins": metrics.get("day_wins", 0),
        "day_win_rate_pct": metrics.get("day_win_rate_pct", 0.0),
        "asset_trades": metrics.get("asset_trades", 0),
        "asset_wins": metrics.get("asset_wins", 0),
        "asset_win_rate_pct": metrics.get("asset_win_rate_pct", 0.0),
        "profit_factor": metrics.get("profit_factor", "n/a"),
        "max_drawdown_pct": metrics.get("max_drawdown_pct", 0.0),
        "sharpe_ratio": metrics.get("sharpe_ratio", 0.0),
    }

    if persist:
        if trades:
            pd.DataFrame([t.to_dict() for t in trades]).to_csv(
                OUT_DIR / f"trades_{tag}.csv", index=False
            )
        if equity_curve:
            pd.DataFrame([e.to_dict() for e in equity_curve]).to_csv(
                OUT_DIR / f"equity_{tag}.csv", index=False
            )

    print(
        f"  {label:16s} | {row['sessions']:3d} sessions | "
        f"trade days {row['trade_days']:2d} | "
        f"return {row['total_return_pct']:+9.2f}% | "
        f"day WR {row['day_win_rate_pct']:6.2f}% | "
        f"maxDD {row['max_drawdown_pct']:7.2f}% | "
        f"final ${row['final_equity']:,.0f}"
    )
    return row


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()

    print("=" * 96)
    print("AGBA METTA MODEL - MONTHLY BACKTEST, JANUARY 2026 -> JUNE 2026")
    print("=" * 96)
    print(f"Model            : {config.model.name} v{config.model.version}")
    print(f"Initial capital  : ${config.backtest.initial_capital:,.0f} (reset each month)")
    print(
        f"Risk/trade       : {config.position_sizing.risk_per_trade_pct * 100:.0f}% | "
        f"Leverage {config.position_sizing.leverage}x | "
        f"Hard stop {config.risk.hard_stop_pct * 100:.0f}%"
    )
    print(
        "Data             : COMEX GC=F, CME 6E=F, CME 6A=F daily OHLC + FRED DFII10 "
        "(real, cached in data/raw/)"
    )
    print("-" * 96)

    rows = []
    for ym, label in MONTHS:
        start, end = month_bounds(ym)
        row = run_window(config, label, start, end, ym)
        if row:
            rows.append(row)

    print("-" * 96)
    continuous = run_window(
        config, "2026 H1 (compounded)", "2026-01-01", "2026-06-30", "2026H1"
    )
    print("=" * 96)

    all_rows = rows + ([continuous] if continuous else [])
    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_DIR / "monthly_summary.csv", index=False)

    payload = {
        "model": f"{config.model.name} v{config.model.version}",
        "period": "2026-01-01 to 2026-06-30",
        "capital_treatment": "each month restarts from initial capital; "
                             "the H1 row compounds across the whole window",
        "data_sources": {
            "gold": "COMEX front-month gold future (Yahoo Finance GC=F), daily OHLC",
            "eur": "CME front-month Euro FX future (Yahoo Finance 6E=F), daily OHLC",
            "aud": "CME front-month AUD future (Yahoo Finance 6A=F), daily OHLC",
            "real_yield": "FRED DFII10, 10-Year TIPS constant-maturity real yield",
        },
        "config": {
            "risk_per_trade_pct": config.position_sizing.risk_per_trade_pct,
            "leverage": config.position_sizing.leverage,
            "hard_stop_pct": config.risk.hard_stop_pct,
            "max_drawdown_pct": config.risk.max_drawdown_pct,
            "contraction_yield_threshold": config.regime.contraction_yield_threshold,
            "expansion_yield_threshold": config.regime.expansion_yield_threshold,
            "entry": config.execution.entry,
            "exit": config.execution.exit,
        },
        "months": rows,
        "continuous_h1": continuous,
    }
    (OUT_DIR / "monthly_summary.json").write_text(json.dumps(payload, indent=2, default=str))

    print(f"Wrote {(OUT_DIR / 'monthly_summary.csv').relative_to(ROOT)}")
    print(f"Wrote {(OUT_DIR / 'monthly_summary.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
