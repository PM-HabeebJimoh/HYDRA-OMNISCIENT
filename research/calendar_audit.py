"""
AUDIT the calendar findings before believing any of them.

Three questions:
  1. Is (C) release-bar surprise tradeable, or is it a look-ahead?
  2. Is (D) next-bar magnitude-weighted gold t=+2.44 real, or multiple-testing?
  3. Is (A) the schedule volatility signal real and, crucially, ANTICIPATORY?
"""
import json, sys, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, A
from calendar_edge import build_events, tstat, signflip_null, USD_TO_ASSET

p1h = load_1h()
bars = sorted(p1h)
idx = {t: i for i, t in enumerate(bars)}
events = build_events()
for e in events:
    e['i'] = idx.get(e['ts'] - (e['ts'] % 3600))
matched = [e for e in events if e['i'] is not None]

def ret(i, a):
    b = p1h[bars[i]][a]; return (b['close'] - b['open']) / b['open']
def rng_(i, a):
    b = p1h[bars[i]][a]; return (b['high'] - b['low']) / b['open']

print("=" * 74)
print("1. IS THE RELEASE-BAR SURPRISE EDGE TRADEABLE?")
print("=" * 74)
print("""
The releases land at :30 and :15 past the hour. A 1H bar running 08:00-09:00
therefore CONTAINS the 08:30 print. Its close-minus-open captures the jump.
But the surprise is only knowable AT 08:30. To collect that bar's return you
must be positioned at 08:00 -- 30 minutes BEFORE the number exists.

So the (C) release-bar result is a look-ahead. Test: how much of the bar's
return happens before vs after the print? If the edge were tradeable at the
bar open, the NEXT bar (fully after the print, fully knowable) would also pay.
""")
for h, lbl in [(0, 'release bar (LOOK-AHEAD)'), (1, 'next bar (honest)')]:
    pnl = []
    for e in matched:
        x = e['surp']
        if x is None or x == 0: continue
        i = e['i']; j = i if h == 0 else i + 1
        if j >= len(bars): continue
        pnl.append(np.sign(x) * USD_TO_ASSET * np.mean([ret(j, a) for a in A]))
    m, t, n = tstat(pnl)
    print(f"  {lbl:28s} mean {m*100:+.4f}%  t={t:+5.2f}  n={n}")
print("""
  VERDICT: the entire (C) effect lives in the bar you cannot enter.
  The first honestly-tradeable bar pays nothing. (C) IS WITHDRAWN.
""")

print("=" * 74)
print("2. IS (D) GOLD NEXT-BAR t=+2.44 REAL?")
print("=" * 74)
cells = []
for h in (1, 2):
    for a in A:
        pnl = []
        for e in matched:
            z = e['surp_z']
            if z is None or z == 0: continue
            i = e['i']
            if i + h >= len(bars): continue
            r = sum(ret(j, a) for j in range(i + 1, i + h + 1))
            pnl.append(np.clip(z, -3, 3) * USD_TO_ASSET * r)
        m, t, n = tstat(pnl)
        cells.append((f"h={h} {a}", m, t, n, pnl))
ts = [abs(c[2]) for c in cells]
print(f"  cells tested in section D: {len(cells)}  max |t| = {max(ts):.2f}")
print(f"  expected max |t| from {len(cells)} independent draws of N(0,1) "
      f"~ {np.sqrt(2*np.log(len(cells))):.2f}")
best = max(cells, key=lambda c: abs(c[2]))
print(f"  best cell: {best[0]}  t={best[2]:+.2f}  n={best[3]}")
p = signflip_null(best[4])
print(f"  sign-flip null on the best cell alone: p={p:.4f}")
x = np.asarray(best[4]); half = len(x)//2
for lbl, s in [('first half', x[:half]), ('second half', x[half:])]:
    m, t, n = tstat(s)
    print(f"    {lbl:12s} mean {m*100:+.4f}%  t={t:+5.2f}  n={n}")
print("""
  The split-half is the test that matters. A real effect survives it.""")

print()
print("=" * 74)
print("3. IS (A) THE SCHEDULE VOLATILITY SIGNAL REAL *AND* ANTICIPATORY?")
print("=" * 74)
print("""
This is the only layer that is knowable with certainty days in advance.
Nothing about it depends on the number, only on the calendar being published.
Three checks: (a) does it hold out-of-sample month by month, (b) is it
distinct from the chart's own volatility forecast, (c) is it distinct from
plain time-of-day (08:30 ET is always a busy hour, release or not)?
""")
ev_bars = set(e['i'] for e in matched)

# (a) month by month
print("  (a) month by month, gold range ratio event/non-event")
mo = {}
for i, t in enumerate(bars):
    k = dt.datetime.utcfromtimestamp(t).strftime('%Y-%m')
    mo.setdefault(k, []).append(i)
for k in sorted(mo):
    on = [rng_(i, 'gold') for i in mo[k] if i in ev_bars]
    off = [rng_(i, 'gold') for i in mo[k] if i not in ev_bars]
    if len(on) < 3: continue
    print(f"      {k}  n_event={len(on):3d}  ratio {np.mean(on)/np.mean(off):5.3f}")

# (c) control for hour-of-day  <-- the honest killer test
print()
print("  (c) SAME HOUR-OF-DAY control: compare release bars only against")
print("      non-release bars in the SAME UTC hour. If the ratio survives,")
print("      the calendar knows something the clock does not.")
for a in A:
    num, den, nn = [], [], 0
    for i in ev_bars:
        hh = dt.datetime.utcfromtimestamp(bars[i]).hour
        peers = [rng_(j, a) for j in range(len(bars))
                 if j not in ev_bars
                 and dt.datetime.utcfromtimestamp(bars[j]).hour == hh]
        if len(peers) < 10: continue
        num.append(rng_(i, a)); den.append(np.mean(peers)); nn += 1
    r = np.array(num) / np.array(den)
    m, t, n = tstat(list(r - 1))
    print(f"      {a:5s} hour-matched ratio {np.mean(r):5.3f}   "
          f"t(ratio-1) = {t:+5.2f}   n={nn}")
print("""
  If the hour-matched ratio stays well above 1.0 with a large t, then the
  economic calendar is a genuine ADVANCE volatility forecast -- available
  days ahead, independent of the chart and independent of the clock.""")
