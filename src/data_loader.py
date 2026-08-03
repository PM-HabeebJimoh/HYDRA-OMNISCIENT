"""
Agba Metta Model - Real Data Loader

Reads the real market-data panel produced by scripts/build_dataset.py. Every
value traces back to a provider payload cached under data/raw/:

  * gold       XAUUSD spot   (Investing.com pair 68)
  * eur        EURUSD spot   (Investing.com pair 1)
  * aud        AUDUSD spot   (Investing.com pair 5)
  * real_yield FRED DFII10 10-Year TIPS real yield

SPOT, not futures - the same series the July 2026 reference backtest used.

There are no hardcoded, synthetic or placeholder prices in this module. If the
panel is missing the loader raises rather than falling back to invented data.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "market_data_spot.json"

REQUIRED_FIELDS = ("open", "high", "low", "close")


@lru_cache(maxsize=1)
def load_real_ohlc_data() -> Dict[str, dict]:
    """Load the full real market-data panel, keyed by session date."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Real market data panel not found at {DATA_FILE}. "
            "Run: python3 scripts/build_spot_dataset.py"
        )

    with DATA_FILE.open() as fh:
        panel = json.load(fh)

    _validate(panel)
    return panel


def _validate(panel: Dict[str, dict]) -> None:
    """Fail loudly on missing or structurally impossible bars."""
    if not panel:
        raise ValueError("Market data panel is empty.")

    for date, row in panel.items():
        if "real_yield" not in row or row["real_yield"] is None:
            raise ValueError(f"{date}: missing real_yield")
        for asset in ("gold", "eur", "aud"):
            bar = row.get(asset)
            if bar is None:
                raise ValueError(f"{date}: missing {asset} bar")
            for field in REQUIRED_FIELDS:
                if bar.get(field) is None:
                    raise ValueError(f"{date}: {asset} missing {field}")
            lo, hi = bar["low"], bar["high"]
            if lo > hi or not (lo <= bar["open"] <= hi) or not (lo <= bar["close"] <= hi):
                raise ValueError(f"{date}: {asset} has inconsistent OHLC {bar}")


def load_market_data_for_backtest(start_date: str, end_date: str) -> Dict[str, dict]:
    """Return the real panel restricted to [start_date, end_date] inclusive."""
    panel = load_real_ohlc_data()
    return {
        date: row
        for date, row in sorted(panel.items())
        if start_date <= date <= end_date
    }


if __name__ == "__main__":
    data = load_real_ohlc_data()
    dates = sorted(data)
    print(f"Loaded {len(dates)} real trading sessions: {dates[0]} -> {dates[-1]}")
    for date in dates[:5]:
        d = data[date]
        print(
            f"  {date}: Gold={d['gold']['close']:.2f}, "
            f"EUR={d['eur']['close']:.5f}, AUD={d['aud']['close']:.5f}, "
            f"Yield={d['real_yield']:.2f}%"
        )
