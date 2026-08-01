"""
TRUE OUT-OF-SAMPLE TEST of "COT spec-net percentile extreme -> FOLLOW".

In-sample (Dec 2025 - Jul 2026, the window everything else in this project
used): t=+2.36 raw, t=+2.79 collapsing correlated legs, sign-flip p=0.0065.
BUT family-wise p=0.1027 once the 16-cell search is accounted for.

Family-wise correction says "not proven", not "false". The only way to settle
it is data the signal has never seen. So: 352 weeks of CFTC gold COT
(Dec 2018 - Aug 2025) against weekly Investing.com gold closes.

That is 7 years x 52 = ~350 independent weekly observations vs 32 in sample.
No parameter is refit. The rule is frozen exactly as specified in sample:
    pct = rank of spec net within PRIOR history (expanding, >=12 obs)
    pct > 0.8 -> LONG ;  pct < 0.2 -> SHORT ;  else flat
    enter the week AFTER the Friday publication, hold 1 week
"""
import csv, json, sys, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'research'))
from calendar_edge import tstat, signflip_null

# ---------- COT (real CFTC, transcribed from the Socrata CSV endpoint)
rows = []
with open(ROOT / 'data/raw/oos/cot_gold_hist.csv') as f:
    for r in csv.DictReader(f):
        rows.append((dt.date.fromisoformat(r['d']),
                     int(r['nl']) - int(r['ns'])))
rows.sort()
print(f"COT gold weeks: {len(rows)}  {rows[0][0]} .. {rows[-1][0]}")

# ---------- weekly gold closes (Investing.com pid 68, resolution=W)
W = json.load(open(ROOT / 'data/raw/oos/gold_weekly.json'))
px = {dt.date.fromtimestamp(t): c for t, c in zip(W['t'], W['c'])}
pxd = sorted(px)
print(f"weekly gold bars: {len(pxd)}  {pxd[0]} .. {pxd[-1]}")

def close_on_or_after(d):
    for x in pxd:
        if x >= d:
            return x, px[x]
    return None, None

def week_ret(pub):
    """Return of the week that STARTS after publication (Friday)."""
    d0, p0 = close_on_or_after(pub)
    if d0 is None: return None
    nxt = [x for x in pxd if x > d0]
    if not nxt: return None
    return (px[nxt[0]] - p0) / p0

# ---------- frozen rule
pnl, hist, used = [], [], []
for asof, net in rows:
    pub = asof + dt.timedelta(days=3)           # Tuesday as-of -> Friday pub
    if len(hist) >= 12:
        pct = float(np.mean([h < net for h in hist]))
        s = 1 if pct > 0.8 else (-1 if pct < 0.2 else 0)
        if s:
            r = week_ret(pub)
            if r is not None:
                pnl.append(s * r); used.append((asof, s, r))
    hist.append(net)

m, t, n = tstat(pnl)
print()
print("=" * 74)
print("OUT-OF-SAMPLE RESULT (Dec 2018 - Aug 2025, gold, frozen rule)")
print("=" * 74)
print(f"  n = {n} weekly trades")
print(f"  mean {m*100:+.4f}% per week   t = {t:+.2f}   "
      f"WR {np.mean([v>0 for v in pnl])*100:.1f}%")
print(f"  sign-flip p = {signflip_null(pnl):.4f}")
print(f"  in-sample was: mean +0.475%, t=+2.79, WR 62.5%, n=32")

# year by year
print()
print("  year by year:")
byy = {}
for (asof, s, r), v in zip(used, pnl):
    byy.setdefault(asof.year, []).append(v)
pos = 0
for y in sorted(byy):
    mm, tt, nn = tstat(byy[y])
    pos += mm > 0
    print(f"    {y}  n={nn:3d}  mean {mm*100:+.4f}%  t={tt:+5.2f}")
print(f"    -> {pos} of {len(byy)} years positive")

# long vs short legs
print()
lo = [v for (a, s, r), v in zip(used, pnl) if s > 0]
sh = [v for (a, s, r), v in zip(used, pnl) if s < 0]
for lab, v in [('LONG legs ', lo), ('SHORT legs', sh)]:
    mm, tt, nn = tstat(v)
    print(f"  {lab}  n={nn:3d}  mean {mm*100:+.4f}%  t={tt:+5.2f}")

# benchmark: was gold just going up?
bench = []
for asof, net in rows:
    r = week_ret(asof + dt.timedelta(days=3))
    if r is not None: bench.append(r)
mb, tb, nb = tstat(bench)
print()
print(f"  buy-and-hold gold, same weeks: mean {mb*100:+.4f}%  t={tb:+.2f}  n={nb}")
print(f"  signal minus benchmark: {(m-mb)*100:+.4f}% per week")

print()
print("=" * 74)
print("VERDICT")
print("=" * 74)
if abs(t) < 1.96:
    print(f"  t = {t:+.2f} out of sample on n={n}. The in-sample t=+2.79 does")
    print("  NOT replicate. Combined with family-wise p=0.1027, this is the")
    print("  34th direction test to fail. WITHDRAWN.")
else:
    print(f"  t = {t:+.2f} out of sample on n={n} -- IT REPLICATES.")
