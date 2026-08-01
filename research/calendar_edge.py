"""
THE PRE-CHART LAYER: Investing.com economic calendar.

Everything tested here is data that exists BEFORE the chart moves:
  A) SCHEDULE      - known days/weeks ahead. Which bars will have a release.
  B) FORECAST-PREV - consensus published days ahead. Ex-ante expected change.
  C) SURPRISE      - actual minus forecast, known at the release instant.
  D) DRIFT         - does the surprise still pay in bars AFTER the release?

Real data only:
  prices  : data/raw/intraday  (Investing.com 1H OHLC, XAUUSD/EURUSD/AUDUSD)
  events  : data/raw/calendar/us_events.json (Investing.com calendar pages)

Null control = sign-flip (order-invariance makes shuffling meaningless on
compounded products; the prior session already established this).
"""
import json, glob, collections, datetime as dt, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from intraday_engine import load_1h, resample_4h, A

CAL = json.load(open(ROOT / 'data/raw/calendar/us_events.json'))
EV, SIGN = CAL['events'], CAL['_usd_sign']

# XAUUSD/EURUSD/AUDUSD are all quoted vs USD -> a USD-bullish surprise pushes
# all three DOWN. So asset direction = -1 * usd_direction.
USD_TO_ASSET = -1


def et_to_utc(datestr, timestr):
    """Investing.com displays US Eastern. 2025-12..2026-08 window:
    EST(UTC-5) before 2026-03-08, EDT(UTC-4) from 2026-03-08 to 2026-11-01."""
    d = dt.date.fromisoformat(datestr)
    hh, mm = map(int, timestr.split(':'))
    edt = dt.date(2026, 3, 8) <= d < dt.date(2026, 11, 1)
    off = 4 if edt else 5
    naive = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=dt.timezone.utc)
    return int((naive + dt.timedelta(hours=off)).timestamp())


def build_events():
    """One row per (event, release). Returns list of dicts with real fields."""
    out = []
    for name, rows in EV.items():
        s = SIGN[name]
        # scale so surprises are comparable across series: use the series' own
        # historical |actual| dispersion (computed from THIS window only, and
        # only from releases strictly before the row -> no look-ahead).
        hist = []
        for datestr, timestr, a, f, p in sorted(rows, key=lambda r: r[0]):
            ts = et_to_utc(datestr, timestr)
            row = dict(name=name, date=datestr, ts=ts, sign=s,
                       actual=a, fcst=f, prev=p)
            # B) ex-ante: forecast vs previous, known days before release
            row['exante'] = (f - p) * s if (f is not None and p is not None) else None
            # C) surprise: actual vs forecast, known at release instant
            if a is not None and f is not None:
                raw = (a - f) * s
                sd = np.std(hist) if len(hist) >= 3 else None
                row['surp'] = raw
                row['surp_z'] = (raw / sd) if (sd and sd > 0) else None
                hist.append(raw)   # append AFTER, so z uses only prior releases
            else:
                row['surp'] = row['surp_z'] = None
            out.append(row)
    return sorted(out, key=lambda r: r['ts'])


def tstat(x):
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)], float)
    if len(x) < 3:
        return np.nan, np.nan, len(x)
    return x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(len(x))), len(x)


def signflip_null(x, nsim=20000, seed=0):
    """Valid null: the magnitudes are real, only the signs are randomised."""
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)], float)
    if len(x) < 3:
        return np.nan
    rng = np.random.default_rng(seed)
    obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))
    flips = rng.choice([-1.0, 1.0], size=(nsim, len(x)))
    sim = flips * x
    m = sim.mean(1)
    s = sim.std(1, ddof=1) / np.sqrt(len(x))
    return float((np.abs(m / s) >= obs).mean())


def main():
    p1h = load_1h()
    bars = sorted(p1h)
    print(f"1H bars (3-asset complete): {len(bars)}  "
          f"{dt.datetime.utcfromtimestamp(bars[0]):%Y-%m-%d} .. "
          f"{dt.datetime.utcfromtimestamp(bars[-1]):%Y-%m-%d}")

    events = build_events()
    print(f"calendar releases transcribed: {len(events)}")

    # map each event to the 1H bar that CONTAINS it, and the following bars
    idx = {t: i for i, t in enumerate(bars)}
    def bar_of(ts):
        b = ts - (ts % 3600)
        return idx.get(b)

    matched = []
    for e in events:
        i = bar_of(e['ts'])
        if i is not None:
            e['i'] = i
            matched.append(e)
    print(f"releases landing inside a complete 3-asset 1H bar: {len(matched)}")
    print()

    def ret(i, a):
        b = p1h[bars[i]][a]
        return (b['close'] - b['open']) / b['open']

    def rng_(i, a):
        b = p1h[bars[i]][a]
        return (b['high'] - b['low']) / b['open']

    # ---------------------------------------------------------------- A
    print("=" * 74)
    print("A) SCHEDULE ONLY  (known days ahead: is there a release this bar?)")
    print("=" * 74)
    ev_bars = set(e['i'] for e in matched)
    for a in A:
        on = [rng_(i, a) for i in ev_bars]
        off = [rng_(i, a) for i in range(len(bars)) if i not in ev_bars]
        d_on, d_off = np.mean(on), np.mean(off)
        # Welch t
        t = (d_on - d_off) / np.sqrt(np.var(on, ddof=1) / len(on)
                                     + np.var(off, ddof=1) / len(off))
        print(f"  {a:5s} range  event bar {d_on*100:6.3f}%   "
              f"non-event {d_off*100:6.3f}%   ratio {d_on/d_off:5.3f}  t={t:+6.2f}")
    # direction on event bars
    for a in A:
        r = [ret(i, a) for i in ev_bars]
        m, t, n = tstat(r)
        print(f"  {a:5s} DIRECTION on event bars: mean {m*100:+.4f}%  t={t:+5.2f}  n={n}")
    print()

    # ---------------------------------------------------------------- B
    print("=" * 74)
    print("B) EX-ANTE  forecast minus previous (published DAYS before release)")
    print("   Fully anticipatory: nothing here is known only at release time.")
    print("=" * 74)
    for horizon, lbl in [(0, 'release bar'), (1, 'next bar'), (4, 'next 4 bars')]:
        for a in A:
            pnl = []
            for e in matched:
                x = e['exante']
                if x is None or x == 0:
                    continue
                i = e['i']
                if horizon == 0:
                    j0, j1 = i, i
                else:
                    j0, j1 = i + 1, i + horizon
                if j1 >= len(bars):
                    continue
                r = sum(ret(j, a) for j in range(j0, j1 + 1))
                pnl.append(np.sign(x) * USD_TO_ASSET * r)
            m, t, n = tstat(pnl)
            print(f"  {lbl:12s} {a:5s} mean {m*100:+.4f}%  t={t:+5.2f}  n={n}")
        print()

    # ---------------------------------------------------------------- C
    print("=" * 74)
    print("C) SURPRISE  actual minus forecast (known at the release instant)")
    print("=" * 74)
    for horizon, lbl in [(0, 'release bar'), (1, 'next bar'),
                         (2, 'next 2 bars'), (6, 'next 6 bars')]:
        for a in A:
            pnl = []
            for e in matched:
                x = e['surp']
                if x is None or x == 0:
                    continue
                i = e['i']
                j0, j1 = (i, i) if horizon == 0 else (i + 1, i + horizon)
                if j1 >= len(bars):
                    continue
                r = sum(ret(j, a) for j in range(j0, j1 + 1))
                pnl.append(np.sign(x) * USD_TO_ASSET * r)
            m, t, n = tstat(pnl)
            star = ' ***' if abs(t) > 1.96 else ''
            print(f"  {lbl:12s} {a:5s} mean {m*100:+.4f}%  t={t:+5.2f}  n={n}{star}")
        print()

    # ---------------------------------------------------------------- D
    print("=" * 74)
    print("D) MAGNITUDE-WEIGHTED SURPRISE (z-scored on prior releases only)")
    print("=" * 74)
    for horizon, lbl in [(0, 'release bar'), (1, 'next bar'), (2, 'next 2 bars')]:
        for a in A:
            pnl = []
            for e in matched:
                z = e['surp_z']
                if z is None or z == 0:
                    continue
                i = e['i']
                j0, j1 = (i, i) if horizon == 0 else (i + 1, i + horizon)
                if j1 >= len(bars):
                    continue
                r = sum(ret(j, a) for j in range(j0, j1 + 1))
                pnl.append(np.clip(z, -3, 3) * USD_TO_ASSET * r)
            m, t, n = tstat(pnl)
            star = ' ***' if abs(t) > 1.96 else ''
            print(f"  {lbl:12s} {a:5s} mean {m*100:+.4f}%  t={t:+5.2f}  n={n}{star}")
        print()

    # ---------------------------------------------------------------- E
    print("=" * 74)
    print("E) BASKET: trade all 3 assets on the surprise, release bar + next")
    print("=" * 74)
    for horizon in (0, 1, 2, 3):
        pnl = []
        for e in matched:
            x = e['surp']
            if x is None or x == 0:
                continue
            i = e['i']
            j0, j1 = (i, i) if horizon == 0 else (i + 1, i + horizon)
            if j1 >= len(bars):
                continue
            r = np.mean([sum(ret(j, a) for j in range(j0, j1 + 1)) for a in A])
            pnl.append(np.sign(x) * USD_TO_ASSET * r)
        m, t, n = tstat(pnl)
        p = signflip_null(pnl)
        wr = np.mean([v > 0 for v in pnl]) * 100 if pnl else np.nan
        print(f"  h={horizon}  mean {m*100:+.4f}%  t={t:+5.2f}  n={n}  "
              f"WR {wr:5.1f}%  sign-flip p={p:.4f}")
    print()


if __name__ == '__main__':
    main()
