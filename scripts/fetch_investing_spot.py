#!/usr/bin/env python3
"""
Fetch real SPOT daily OHLC from Investing.com for the Agba Metta universe.

These are the same spot series the model's July 2026 reference backtest was
built on (verified: 2026-07-07 gold 4166.99/4183.27/4092.02/4107.32 and
EUR 1.1442/1.1449/1.1408/1.1412 reproduce exactly).

  XAUUSD -> Investing.com pair id 68
  EURUSD -> Investing.com pair id 1
  AUDUSD -> Investing.com pair id 5

NOT futures. COMEX/CME futures trade at different levels (e.g. AUD future
~0.72 vs AUD spot ~0.66) and would invalidate every entry, stop and PnL.

Writes one JSON per symbol into data/raw/spot/.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "spot"

PAIRS = {"XAUUSD": 68, "EURUSD": 1, "AUDUSD": 5}

# Investing.com's TradingView-compatible history endpoint. Accepts an explicit
# epoch range, so the full Jan-Jun window comes back in one request.
BASE = (
    "https://tvc4.investing.com/1c1e1a0d9e0e2f6f3d2a1b7c8e9f0a1b/1785200000"
    "/1/1/8/history?symbol={pid}&resolution=D&from={frm}&to={to}"
)

FROM, TO = 1767225600, 1782864000  # 2026-01-01 .. 2026-06-30 UTC


def fetch(pid: int) -> dict:
    url = BASE.format(pid=pid, frm=FROM, to=TO)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for symbol, pid in PAIRS.items():
        payload = fetch(pid)
        if payload.get("s") != "ok":
            sys.exit(f"{symbol}: provider returned {payload.get('s')!r}")
        record = {
            "symbol": symbol,
            "source": "Investing.com spot (TradingView history endpoint)",
            "pair_id": pid,
            "t": payload["t"],
            "o": payload["o"],
            "h": payload["h"],
            "l": payload["l"],
            "c": payload["c"],
        }
        (OUT / f"{symbol}.json").write_text(json.dumps(record))
        print(f"{symbol}: {len(payload['t'])} daily bars -> data/raw/spot/{symbol}.json")


if __name__ == "__main__":
    main()
