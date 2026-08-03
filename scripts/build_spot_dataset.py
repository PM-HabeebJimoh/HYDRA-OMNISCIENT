#!/usr/bin/env python3
"""
Build the Agba Metta market-data panel from REAL SPOT prices.

  XAUUSD  Investing.com spot, pair id 68
  EURUSD  Investing.com spot, pair id 1
  AUDUSD  Investing.com spot, pair id 5
  yield   FRED DFII10, 10Y TIPS constant-maturity real yield

These are the same spot series the model's July 2026 reference backtest used.
Futures are deliberately NOT used: CME/COMEX contracts trade at different
levels (AUD future ~0.72 vs AUD spot ~0.66), which would corrupt every entry,
stop and PnL.

Raw provider payloads are cached verbatim in data/raw/spot/. This script only
reshapes them: epoch -> date, parallel arrays -> OHLC records, as-of join of
the real yield. Nothing is invented, interpolated or smoothed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SPOT = RAW / "spot"
OUT = ROOT / "data" / "market_data_spot.json"

ASSETS = {"gold": "XAUUSD", "eur": "EURUSD", "aud": "AUDUSD"}


def load_symbol(symbol: str) -> dict[str, dict]:
    """Merge every cached window for one spot symbol into date -> OHLC."""
    bars: dict[str, dict] = {}
    for path in sorted(SPOT.glob(f"{symbol}*.json")):
        p = json.loads(path.read_text())
        for ts, o, h, l, c in zip(p["t"], p["o"], p["h"], p["l"], p["c"]):
            if None in (o, h, l, c):
                continue
            date = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
            bars[date] = {
                "open": round(float(o), 6),
                "high": round(float(h), 6),
                "low": round(float(l), 6),
                "close": round(float(c), 6),
            }
    return bars


def load_real_yield() -> dict[str, float]:
    series: dict[str, float] = {}
    for line in (RAW / "DFII10.csv").read_text().strip().splitlines()[1:]:
        date, _, value = line.partition(",")
        value = value.strip()
        if value and value != ".":
            series[date.strip()] = float(value)
    return series


def main() -> None:
    assets = {k: load_symbol(sym) for k, sym in ASSETS.items()}
    yields = load_real_yield()
    ykeys = sorted(yields)

    common = sorted(set.intersection(*(set(v) for v in assets.values())))
    panel: dict[str, dict] = {}

    for date in common:
        prior = [k for k in ykeys if k <= date]
        if not prior:
            continue
        bars = {a: assets[a][date] for a in ASSETS}
        # Drop provider rows that are entirely flat (no real session activity).
        if all(b["open"] == b["high"] == b["low"] == b["close"] for b in bars.values()):
            continue
        panel[date] = {
            **{a: {"date": date, **b} for a, b in bars.items()},
            "real_yield": yields[prior[-1]],
        }

    OUT.write_text(json.dumps(panel, indent=2, sort_keys=True))
    dates = sorted(panel)
    print(f"Sessions: {len(panel)}  ({dates[0]} -> {dates[-1]})")
    months: dict[str, int] = {}
    for d in dates:
        months[d[:7]] = months.get(d[:7], 0) + 1
    print("Per month:", months)
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
