"""
TRY TO KILL "3b EXTREME pct>0.8 FOLLOW".

t=+2.36, sign-flip p=0.0172, WR 57.1%, n=63, hold 5 days. First direction
signal to clear 1.96 in 33 tests across 8 data layers. Extraordinary claims
need the full battery, and I have withdrawn six such results already.

Every check below is one that has killed a result in this project before.
"""
import json, sys, collections, datetime as dt, itertools
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, A
from calendar_edge import tstat, signflip_null
from cot_direction import FEAT, fwd_ret, days, daily

def collect(thr_hi, thr_lo, nd=5, assets=A, use_pub=True):
    out = []
    for a in assets:
        for r in FEAT[a]:
            p = r['pct']
            if p is None: continue
            s = 1 if p > thr_hi else (-1 if p < thr_lo else 0)
            if not s: continue
            x = fwd_ret(r['pub'] if use_pub else r['asof'], a, nd)
            if x is None: continue
            out.append((r['pub'], a, s * x, p))
    return out

base = collect(0.8, 0.2)
pnl = [r[2] for r in base]
m, t, n = tstat(pnl)
print("=" * 78)
print(f"BASELINE  n={n}  mean {m*100:+.3f}%  t={t:+.2f}  "
      f"WR {np.mean([v>0 for v in pnl])*100:.1f}%")
print("=" * 78)

# --- 1. MULTIPLE TESTING. How many cells did I really search?
print("\n1. MULTIPLE TESTING")
print("   Section 1 searched 8 angles x 2 horizons = 16 cells.")
print("   This cell is the max of 16. Empirical null: repeat the WHOLE")
print("   16-cell search on sign-flipped returns and record the max |t|.")
rng = np.random.default_rng(0)
# rebuild all 16 cells' pnl vectors once, keyed, so we can flip consistently
from cot_direction import ANGLES, run
cells = []
for nd in (5, 10):
    for lab, fn in ANGLES:
        v = []
        for a in A:
            for r in FEAT[a]:
                s = fn(r)
                if not s: continue
                x = fwd_ret(r['pub'], a, nd)
                if x is None: continue
                v.append((r['pub'], a, s, x))
        cells.append(v)
# flip at the level of the underlying (date,asset) RETURN, so all cells see
# the same flipped world -- this preserves the search structure
keys = sorted({(d, a) for c in cells for d, a, _, _ in c})
maxts = []
for _ in range(4000):
    flip = {k: rng.choice([-1.0, 1.0]) for k in keys}
    best = 0.0
    for c in cells:
        v = [s * x * flip[(d, a)] for d, a, s, x in c]
        if len(v) < 3: continue
        mm = np.mean(v); ss = np.std(v, ddof=1) / np.sqrt(len(v))
        if ss > 0: best = max(best, abs(mm / ss))
    maxts.append(best)
maxts = np.array(maxts)
print(f"   null max|t|: median {np.median(maxts):.2f}  "
      f"95th {np.percentile(maxts,95):.2f}  actual {abs(t):.2f}")
print(f"   FAMILY-WISE p = {(maxts >= abs(t)).mean():.4f}")

# --- 2. Threshold robustness. Was 0.8/0.2 cherry-picked?
print("\n2. THRESHOLD ROBUSTNESS (was 0.8/0.2 special?)")
for hi, lo in [(0.70,0.30),(0.75,0.25),(0.80,0.20),(0.85,0.15),(0.90,0.10)]:
    v = [r[2] for r in collect(hi, lo)]
    mm, tt, nn = tstat(v)
    print(f"   pct>{hi:.2f}/<{lo:.2f}  n={nn:3d}  mean {mm*100:+.3f}%  t={tt:+5.2f}")

# --- 3. Split half in time
print("\n3. SPLIT-HALF IN TIME")
b = sorted(base)
h = len(b)//2
for lab, s in [('first half ', b[:h]), ('second half', b[h:])]:
    v = [r[2] for r in s]
    mm, tt, nn = tstat(v)
    print(f"   {lab}  n={nn:3d}  mean {mm*100:+.3f}%  t={tt:+5.2f}  "
          f"({s[0][0]} .. {s[-1][0]})")

# --- 4. Leave-one-asset-out. Does it depend on a single market?
print("\n4. LEAVE-ONE-ASSET-OUT")
for drop in A:
    keep = [x for x in A if x != drop]
    v = [r[2] for r in collect(0.8, 0.2, assets=keep)]
    mm, tt, nn = tstat(v)
    print(f"   without {drop:5s} n={nn:3d}  mean {mm*100:+.3f}%  t={tt:+5.2f}")

# --- 5. THE CRITICAL ONE: overlapping windows.
print("\n5. OVERLAPPING-WINDOW INFLATION  <-- the likely killer")
print("   COT is WEEKLY (5 trading days apart) and the hold is 5 trading")
print("   days, so consecutive observations are nearly non-overlapping in")
print("   time -- but the 3 assets on the SAME week are highly correlated")
print("   (prior session measured gold/eur 0.492, gold/aud 0.583,")
print("   eur/aud 0.737). The naive t treats 63 obs as independent.")
byweek = collections.defaultdict(list)
for d, a, x, p in base:
    byweek[d].append(x)
wk = [np.mean(v) for _, v in sorted(byweek.items())]
mm, tt, nn = tstat(wk)
print(f"   collapsing each week to ONE observation:")
print(f"   n={nn} weeks  mean {mm*100:+.3f}%  t={tt:+5.2f}  "
      f"WR {np.mean([v>0 for v in wk])*100:.1f}%")
print(f"   sign-flip p = {signflip_null(wk):.4f}")
sizes = collections.Counter(len(v) for v in byweek.values())
print(f"   legs per week: {dict(sizes)}  -> naive n={len(base)} vs "
      f"true independent n={nn}")
print(f"   inflation factor sqrt({len(base)}/{nn}) = "
      f"{np.sqrt(len(base)/nn):.2f}x")

# --- 6. Is it just "gold went up"? Long-only benchmark.
print("\n6. IS IT JUST DRIFT? (signal vs always-long, same weeks/assets)")
sig = [r[2] for r in base]
raw = []
for a in A:
    for r in FEAT[a]:
        p = r['pct']
        if p is None or not (p > 0.8 or p < 0.2): continue
        x = fwd_ret(r['pub'], a, 5)
        if x is not None: raw.append(x)
ms, ts_, _ = tstat(sig); mr, tr, _ = tstat(raw)
print(f"   signal      mean {ms*100:+.3f}%  t={ts_:+5.2f}")
print(f"   always-long mean {mr*100:+.3f}%  t={tr:+5.2f}")
nlong = sum(1 for a in A for r in FEAT[a]
            if r['pct'] is not None and r['pct'] > 0.8)
nshort = sum(1 for a in A for r in FEAT[a]
             if r['pct'] is not None and r['pct'] < 0.2)
print(f"   signal is LONG {nlong} times, SHORT {nshort} times "
      f"-> {'BALANCED' if min(nlong,nshort)/max(nlong,nshort)>0.5 else 'DIRECTIONALLY LOPSIDED'}")
