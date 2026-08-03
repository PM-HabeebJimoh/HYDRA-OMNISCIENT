#!/usr/bin/env python3
"""
Build the real market-data panel for the Agba Metta backtest.

Sources (all real, no synthetic values):
  * Gold   -> COMEX front-month gold future (Yahoo Finance symbol GC=F)
  * Euro   -> CME front-month Euro FX future (Yahoo Finance symbol 6E=F)
  * AUD    -> CME front-month Australian Dollar future (Yahoo Finance symbol 6A=F)
  * Yield  -> FRED DFII10, 10-Year TIPS constant-maturity real yield

Raw provider payloads live in data/raw/ exactly as they were returned by the
provider. This script only reshapes them: epoch timestamps -> exchange-local
session dates, arrays -> per-day OHLC records, and an as-of join of the real
yield onto each trading session.

No value is invented, interpolated or smoothed. A session is written to the
panel only when all three instruments and the real yield are genuinely present.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "market_data_2026.json"

# Yahoo daily bars are stamped at the exchange session open. COMEX/CME are in
# America/New_York; the offset is -5h (EST) or -4h (EDT). 2026 US DST runs
# 2026-03-08 -> 2026-11-01.
DST_START = datetime(2026, 3, 8, 7, tzinfo=timezone.utc).timestamp()
DST_END = datetime(2026, 11, 1, 6, tzinfo=timezone.utc).timestamp()

ASSETS = {
    "gold": ["GC=F_h1.json", "GC=F_h2.json"],
    "eur": ["6E=F_h1.json", "6E=F_h2.json"],
    "aud": ["6A=F_h0.json", "6A=F_h1.json", "6A=F_h2.json"],
}


def session_date(epoch: int) -> str:
    """Convert a Yahoo bar timestamp to its exchange-local session date."""
    offset = -4 if DST_START <= epoch < DST_END else -5
    return datetime.fromtimestamp(epoch, timezone.utc).astimezone(
        timezone(timedelta(hours=offset))
    ).strftime("%Y-%m-%d")


def load_asset(files: list[str]) -> dict[str, dict]:
    """Load and merge one instrument's raw payloads into date -> OHLC."""
    bars: dict[str, dict] = {}
    for name in files:
        payload = json.loads((RAW / name).read_text())
        rows = zip(
            payload["timestamp"],
            payload["open"],
            payload["high"],
            payload["low"],
            payload["close"],
        )
        for ts, o, h, l, c in rows:
            if None in (o, h, l, c):
                continue  # provider gap - never fabricate a bar
            bars[session_date(ts)] = {
                "open": round(float(o), 6),
                "high": round(float(h), 6),
                "low": round(float(l), 6),
                "close": round(float(c), 6),
            }
    return bars


def load_real_yield() -> dict[str, float]:
    """Parse the FRED DFII10 CSV, skipping the '.'/blank holiday rows."""
    series: dict[str, float] = {}
    lines = (RAW / "DFII10.csv").read_text().strip().splitlines()[1:]
    for line in lines:
        date, _, value = line.partition(",")
        value = value.strip()
        if value and value != ".":
            series[date.strip()] = float(value)
    return series


def as_of_yield(date: str, series: dict[str, float], keys: list[str]) -> float | None:
    """Most recent published real yield on or before `date` (no look-ahead)."""
    prior = [k for k in keys if k <= date]
    return series[prior[-1]] if prior else None


def main() -> None:
    assets = {name: load_asset(files) for name, files in ASSETS.items()}
    yields = load_real_yield()
    yield_keys = sorted(yields)

    common = sorted(set.intersection(*(set(v) for v in assets.values())))
    panel: dict[str, dict] = {}
    skipped: list[str] = []

    for date in common:
        if not ("2026-01-01" <= date <= "2026-06-30"):
            continue
        ry = as_of_yield(date, yields, yield_keys)
        if ry is None:
            skipped.append(date)
            continue
        panel[date] = {
            "gold": {"date": date, **assets["gold"][date]},
            "eur": {"date": date, **assets["eur"][date]},
            "aud": {"date": date, **assets["aud"][date]},
            "real_yield": ry,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(panel, indent=2, sort_keys=True))

    dates = sorted(panel)
    print(f"Sessions written : {len(panel)}")
    print(f"Coverage         : {dates[0]} -> {dates[-1]}")
    for name, bars in assets.items():
        in_window = [d for d in bars if "2026-01-01" <= d <= "2026-06-30"]
        print(f"  {name:5s} raw sessions in window: {len(in_window)}")
    if skipped:
        print(f"Skipped (no yield): {skipped}")
    months: dict[str, int] = {}
    for d in dates:
        months[d[:7]] = months.get(d[:7], 0) + 1
    print("Per-month sessions:", months)
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
