#!/usr/bin/env python3
"""
Agba Metta Model v2 — risk-engine enhancements, alignment logic untouched.

v1 (unchanged core, kept exactly):
  * Regime      : DFII10 > 0.7  -> CONTRACTION -> SHORT
  * Alignment   : XAU, EUR, AUD must ALL close < open on the signal day
  * Execution   : enter at that day's open, exit at that day's close
  * Hard stop   : entry x 1.01, checked intraday against the high

v2 additions (risk engine only):
  1. Minimum basket strength      - mean down-move must be >= 0.30%
  2. Volatility-adjusted weights  - XAU shrinks when its ATR is elevated
  3. Dynamic leverage by grade    - A+ 500x / A 300x / B 150x
  4. Basket daily loss limit      - close-out at -10% equity on the day
  5. Post-stop cooldown           - 50% leverage on the next signal
  6. Profit lock                  - risk 20% -> 10% once the month clears +1000%
  7. XAU danger filter            - halve XAU weight after a large upper wick

Every enhancement is switchable so v1 and v2 run through identical code.
"""

from __future__ import annotations

import json
from calendar import monthrange
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ("gold", "eur", "aud")
LABEL = {"gold": "XAUUSD", "eur": "EURUSD", "aud": "AUDUSD"}

# ---------------------------------------------------------------- v2 knobs
MIN_BASKET_STRENGTH = 0.0030   # enhancement 1: mean down-move >= 0.30%
ATR_LOOKBACK        = 14
ATR_HIGH            = 0.0180   # XAU ATR% above this = "high volatility"
ATR_LOW             = 0.0110   # below this = "low volatility"
W_HIGH  = {"gold": 0.150, "eur": 0.425, "aud": 0.425}
W_NORM  = {"gold": 0.250, "eur": 0.375, "aud": 0.375}
W_LOW   = {"gold": 1/3,   "eur": 1/3,   "aud": 1/3}
LEV_A_PLUS, LEV_A, LEV_B = 500, 300, 150
BASKET_MAX_DAILY_LOSS = 0.10   # enhancement 4
COOLDOWN_LEV_MULT     = 0.50   # enhancement 5
PROFIT_LOCK_TRIGGER   = 10.0   # enhancement 6: +1000% within the month
PROFIT_LOCK_RISK      = 0.10
WICK_DANGER           = 0.0060 # enhancement 7: prior upper wick > 0.60%


def load_panel() -> dict:
    """Merge the 2025 and 2026 real-spot panels into one continuous series."""
    panel = {}
    for f in ("data/market_data_spot2025.json", "data/market_data_spot.json"):
        panel.update(json.loads((ROOT / f).read_text()))
    return panel


def atr_pct(panel, dates, i, asset, n=ATR_LOOKBACK):
    """True-range percentage average over the previous n sessions."""
    if i < 1:
        return None
    trs = []
    for j in range(max(1, i - n), i):
        cur, prev = panel[dates[j]][asset], panel[dates[j - 1]][asset]
        tr = max(cur["high"] - cur["low"],
                 abs(cur["high"] - prev["close"]),
                 abs(cur["low"] - prev["close"]))
        trs.append(tr / cur["open"])
    return sum(trs) / len(trs) if trs else None


def grade(strength, xa, yield_rising):
    """Enhancement 3 — setup quality drives leverage."""
    score = 0
    if strength >= 0.0060:            score += 1
    if xa is not None and xa < ATR_HIGH: score += 1
    if yield_rising:                  score += 1
    if score >= 3: return "A+", LEV_A_PLUS
    if score == 2: return "A",  LEV_A
    return "B", LEV_B


def run(version, panel, start, end, capital=100_000.0, base_risk=0.20):
    """Run one month (or any window). version='v1' or 'v2'."""
    dates = sorted(panel)
    win = [d for d in dates if start <= d <= end]
    eq = capital
    peak = capital
    trades, day_rows = [], []
    cooldown = False
    risk = base_risk
    month_start_eq = capital

    for d in win:
        i = dates.index(d)
        r = panel[d]

        # --- v1 core: regime + alignment (identical in both versions) ---
        if not r["real_yield"] > 0.7:
            continue
        if not all(r[a]["close"] < r[a]["open"] for a in ASSETS):
            continue

        strength = sum((r[a]["open"] - r[a]["close"]) / r[a]["open"] for a in ASSETS) / 3

        if version == "v1":
            weights = {a: 1/3 for a in ASSETS}
            lev = 500
            g = "-"
        else:
            # 1. minimum basket strength
            if strength < MIN_BASKET_STRENGTH:
                continue
            # 2. volatility-adjusted weights
            xa = atr_pct(panel, dates, i, "gold")
            if xa is None or xa >= ATR_HIGH:      weights = dict(W_HIGH)
            elif xa <= ATR_LOW:                   weights = dict(W_LOW)
            else:                                 weights = dict(W_NORM)
            # 7. XAU danger filter on the prior upper wick
            if i >= 1:
                p = panel[dates[i - 1]]["gold"]
                wick = (p["high"] - max(p["open"], p["close"])) / p["open"]
                if wick > WICK_DANGER:
                    freed = weights["gold"] * 0.5
                    weights["gold"] -= freed
                    weights["eur"] += freed / 2
                    weights["aud"] += freed / 2
            # 3. dynamic leverage
            prev_y = panel[dates[i - 1]]["real_yield"] if i >= 1 else r["real_yield"]
            g, lev = grade(strength, xa, r["real_yield"] >= prev_y)
            # 5. post-stop cooldown
            if cooldown:
                lev *= COOLDOWN_LEV_MULT
            # 6. profit lock
            risk = PROFIT_LOCK_RISK if (eq / month_start_eq - 1) >= PROFIT_LOCK_TRIGGER else base_risk

        # --- execute the basket ---
        legs, day_pnl, stopped = [], 0.0, False
        for a in ASSETS:
            b = r[a]
            entry = b["open"]
            stop = entry * 1.01
            notional = eq * risk * weights[a] * lev
            if b["high"] >= stop:
                exit_px, reason, stopped = stop, "STOP_LOSS", True
            else:
                exit_px, reason = b["close"], "CLOSE"
            ret = (entry - exit_px) / entry
            pnl = ret * notional
            day_pnl += pnl
            legs.append({"date": d, "asset": LABEL[a], "entry": entry, "stop": stop,
                         "exit": exit_px, "ret_pct": ret * 100, "pnl": pnl,
                         "reason": reason, "weight": weights[a], "lev": lev, "grade": g})

        # 4. basket daily loss limit
        capped = False
        if version == "v2" and day_pnl < -BASKET_MAX_DAILY_LOSS * eq:
            day_pnl = -BASKET_MAX_DAILY_LOSS * eq
            capped = True

        eq += day_pnl
        if eq <= 0:
            eq = 0.0
        cooldown = stopped
        trades.extend(legs)
        peak = max(peak, eq)
        day_rows.append({"date": d, "pnl": day_pnl, "equity": eq,
                         "dd": (eq - peak) / peak * 100 if peak else 0,
                         "capped": capped, "grade": g})
        if eq == 0.0:
            break

    wins = sum(1 for x in day_rows if x["pnl"] > 0)
    return {
        "trade_days": len(day_rows),
        "asset_trades": len(trades),
        "asset_wins": sum(1 for t in trades if t["pnl"] > 0),
        "stops": sum(1 for t in trades if t["reason"] == "STOP_LOSS"),
        "day_win_rate": wins / len(day_rows) * 100 if day_rows else 0.0,
        "return_pct": (eq / capital - 1) * 100,
        "final_equity": eq,
        "max_dd": min([x["dd"] for x in day_rows], default=0.0),
        "capped_days": sum(1 for x in day_rows if x["capped"]),
        "trades": trades, "days": day_rows,
    }


def months(a, b):
    y, m = a
    while (y, m) <= b:
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def main():
    panel = load_panel()
    out = ROOT / "backtest_results" / "v2_comparison"
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 118)
    print("AGBA METTA v1 vs v2 — JANUARY 2025 to JULY 2026 (100% real spot data)")
    print("=" * 118)
    print(f"{'Month':<10}{'v1 days':>8}{'v1 return':>16}{'v1 DD':>9}{'v1 stp':>7}   "
          f"{'v2 days':>8}{'v2 return':>16}{'v2 DD':>9}{'v2 stp':>7}{'v2 grade':>10}")
    print("-" * 118)

    rows = []
    for y, m in months((2025, 1), (2026, 7)):
        s, e = f"{y}-{m:02d}-01", f"{y}-{m:02d}-{monthrange(y, m)[1]:02d}"
        r1, r2 = run("v1", panel, s, e), run("v2", panel, s, e)
        gr = {}
        for t in r2["trades"]:
            gr[t["grade"]] = gr.get(t["grade"], 0) + 1
        gs = ",".join(f"{k}:{v//3}" for k, v in sorted(gr.items()))
        rows.append({"month": f"{y}-{m:02d}", "v1": r1, "v2": r2})
        print(f"{y}-{m:02d}   {r1['trade_days']:>8}{r1['return_pct']:>15,.2f}%"
              f"{r1['max_dd']:>8.2f}%{r1['stops']:>7}   "
              f"{r2['trade_days']:>8}{r2['return_pct']:>15,.2f}%"
              f"{r2['max_dd']:>8.2f}%{r2['stops']:>7}{gs:>10}")

    print("-" * 118)
    c1 = run("v1", panel, "2025-01-01", "2026-07-31")
    c2 = run("v2", panel, "2025-01-01", "2026-07-31")
    print(f"{'COMPOUND':<10}{c1['trade_days']:>8}{c1['return_pct']:>15,.2e}%"
          f"{c1['max_dd']:>8.2f}%{c1['stops']:>7}   "
          f"{c2['trade_days']:>8}{c2['return_pct']:>15,.2e}%"
          f"{c2['max_dd']:>8.2f}%{c2['stops']:>7}")
    print("=" * 118)

    json.dump({"months": [{"month": r["month"],
                           "v1": {k: v for k, v in r["v1"].items() if k not in ("trades", "days")},
                           "v2": {k: v for k, v in r["v2"].items() if k not in ("trades", "days")}}
                          for r in rows],
               "compound": {"v1": {k: v for k, v in c1.items() if k not in ("trades", "days")},
                            "v2": {k: v for k, v in c2.items() if k not in ("trades", "days")}}},
              open(out / "v1_vs_v2.json", "w"), indent=2, default=str)
    return rows, c1, c2


if __name__ == "__main__":
    main()
