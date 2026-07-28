#!/usr/bin/env python3
"""
HYDRA-S3-MAX | Market data normaliser
=====================================
Converts the raw Yahoo Finance v8 chart payloads and the FRED DFII10 series
stored under data/raw/ into a single tidy daily OHLC table used by the
backtest.

Rules
-----
* Every bar keeps its real OHLC — no synthesising of highs/lows.
* A bar is dropped only when the upstream feed itself reports no data
  (null close, or open==high==low==close with zero range which Yahoo emits
  for stale/holiday sessions on the FX crosses).
* Session date is the exchange-local calendar date of the bar timestamp:
  COMEX gold (GC=F) is America/New_York, the FX crosses are Europe/London.
  Using the exchange-local date is what makes the three feeds line up on the
  same trading day.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data")

# Yahoo stamps each daily bar at midnight in the exchange's own timezone, so
# the session date must be recovered with the real tz database (a fixed UTC
# offset silently mis-dates every bar once DST starts).
FEEDS = {
    "XAUUSD": {"file": "yahoo_GC=F_2026H1.json", "tz": "America/New_York"},
    "EURUSD": {"file": "yahoo_EURUSD=X_2026H1.json", "tz": "Europe/London"},
    "AUDUSD": {"file": "yahoo_AUDUSD=X_2026H1.json", "tz": "Europe/London"},
}


def _session_date(epoch: int, tz_name: str) -> str:
    dt = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(ZoneInfo(tz_name))
    return dt.strftime("%Y-%m-%d")


def load_prices() -> pd.DataFrame:
    rows = []
    dropped_flat = 0
    for asset, cfg in FEEDS.items():
        with open(os.path.join(RAW, cfg["file"])) as fh:
            payload = json.load(fh)

        for month, block in payload["months"].items():
            ts = block["timestamp"]
            for i, epoch in enumerate(ts):
                o, h, l, c = (
                    block["open"][i],
                    block["high"][i],
                    block["low"][i],
                    block["close"][i],
                )
                if None in (o, h, l, c):
                    continue
                # Yahoo emits a flat, zero-range bar for stale FX sessions.
                if h == l and o == c and h == o:
                    dropped_flat += 1
                    continue

                # The vendor's daily close is snapped at a slightly different
                # cut-off than the intraday high/low aggregation, so a handful
                # of bars carry a close a fraction of a pip outside the range.
                # Repair the envelope so it contains its own open and close.
                # This only ever widens the range by the already-observed
                # open/close print — no price is invented.
                envelope_fixed = False
                hi = max(h, o, c)
                lo = min(l, o, c)
                if hi != h or lo != l:
                    envelope_fixed = True

                rows.append(
                    {
                        "date": _session_date(epoch, cfg["tz"]),
                        "asset": asset,
                        "open": float(o),
                        "high": float(hi),
                        "low": float(lo),
                        "close": float(c),
                        "vendor_high": float(h),
                        "vendor_low": float(l),
                        "envelope_fixed": envelope_fixed,
                        "source_month": month,
                        "epoch": epoch,
                    }
                )

    df = pd.DataFrame(rows)
    bad = df[(df["high"] < df["low"]) | (df["high"] < df["open"]) | (df["low"] > df["close"])]
    if len(bad):
        raise SystemExit(f"Inconsistent OHLC bars remain after repair:\n{bad}")

    df = df.sort_values(["date", "asset"]).reset_index(drop=True)
    df.attrs["dropped_flat"] = dropped_flat
    return df


def load_yield() -> pd.DataFrame:
    y = pd.read_csv(os.path.join(RAW, "fred_dfii10.csv"))
    y.columns = ["date", "real_yield"]
    y["real_yield"] = pd.to_numeric(y["real_yield"], errors="coerce")
    y = y.dropna(subset=["real_yield"]).reset_index(drop=True)
    return y


def main() -> None:
    prices = load_prices()
    yields = load_yield()

    os.makedirs(OUT, exist_ok=True)
    prices.to_csv(os.path.join(OUT, "ohlc_daily_2026H1.csv"), index=False)
    yields.to_csv(os.path.join(OUT, "real_yield_daily_2026H1.csv"), index=False)

    print("Daily OHLC bars written:", len(prices))
    print("Flat/stale vendor bars dropped:", prices.attrs.get("dropped_flat", 0))
    print("Bars whose high/low envelope was widened to contain open/close:",
          int(prices["envelope_fixed"].sum()))
    for _, r in prices[prices["envelope_fixed"]].iterrows():
        print(
            f"    {r['date']} {r['asset']}: vendor H/L "
            f"{r['vendor_high']:.6f}/{r['vendor_low']:.6f} → {r['high']:.6f}/{r['low']:.6f}"
        )
    for asset, grp in prices.groupby("asset"):
        print(
            f"  {asset:7s} {len(grp):3d} sessions  "
            f"{grp['date'].min()} → {grp['date'].max()}"
        )
    print("Real-yield observations:", len(yields))
    print(
        "  DFII10 range:",
        f"{yields['real_yield'].min():.2f}% → {yields['real_yield'].max():.2f}%",
    )

    # Sessions where all three assets have a real bar — the tradable universe.
    piv = prices.pivot_table(index="date", columns="asset", values="close", aggfunc="last")
    complete = piv.dropna()
    complete = complete[(complete.index >= "2026-01-01") & (complete.index <= "2026-06-30")]
    print("Sessions with all 3 assets (Jan–Jun 2026):", len(complete))


if __name__ == "__main__":
    main()
