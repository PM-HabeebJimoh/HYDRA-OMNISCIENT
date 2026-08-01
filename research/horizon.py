"""
THE FREQUENCY MISMATCH -- a real hole in everything I have done.

Every direction test in this project predicted the NEXT BAR: 1H, 4H, or 1 day.
But the forces I kept saying "shape direction" -- real yields, positioning,
the macro cycle -- move on WEEKS TO MONTHS. Asking a quarterly variable to
predict the next 4 hours is a frequency mismatch, and I never once tested the
horizon it actually operates on.

Also: 8 months of 3 correlated USD pairs is a thin slice. This uses
  * 348 weeks of gold (Jan 2019 - Sep 2025)   Investing.com
  * 400 weeks of DFII10 real 10y yield        FRED
  * 352 weeks of CFTC gold positioning        CFTC
  * weekly VIX/DXY where available
covering COVID, the 2022 hiking cycle, 2023 banking stress, the 2024-25 bull.
That is a 7.6-year, multi-regime, out-of-sample window -- not 8 months.

Tested at horizons 1, 2, 4, 8, 13, 26 weeks. Walk-forward. Sign-flip nulls.
"""
import json, sys, collections, csv, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'research'))
from calendar_edge import tstat, signflip_null

def say(*a): print(*a, flush=True)

# ---------- gold weekly (real Investing.com)
W = json.load(open(ROOT / 'data/raw/oos/gold_weekly.json'))
gold = {dt.date.fromtimestamp(t): c for t, c in zip(W['t'], W['c'])}
gd = sorted(gold)

# ---------- real yield weekly (real FRED)
RY = json.load(open(ROOT / 'data/raw/weekly/DFII10_W.json'))
ry = {dt.date.fromisoformat(x): v for x, v in zip(RY['dates'], RY['v'])}

# ---------- COT gold weekly (real CFTC)
cotrows = []
with open(ROOT / 'data/raw/oos/cot_gold_hist.csv') as f:
    for r in csv.DictReader(f):
        cotrows.append((dt.date.fromisoformat(r['d']),
                        int(r['nl']) - int(r['ns'])))
cotrows.sort()

def latest(mapping, d, maxlag=14):
    """Most recent value strictly before d, within maxlag days."""
    best, bd = None, None
    for k in sorted(mapping):
        if k < d:
            best, bd = mapping[k], k
        else:
            break
    if bd is None or (d - bd).days > maxlag:
        return None
    return best

def cot_pct(d):
    """Percentile of spec net vs prior history, published-Friday lagged."""
    hist, cur = [], None
    for asof, net in cotrows:
        if asof + dt.timedelta(days=3) < d:
            hist.append(net); cur = net
        else:
            break
    if cur is None or len(hist) < 26:
        return None
    return float(np.mean([h < cur for h in hist[:-1]]))

say(f"gold weeks {len(gd)}  {gd[0]} .. {gd[-1]}")
say(f"real-yield weeks {len(ry)}   COT weeks {len(cotrows)}")

# ---------- build weekly panel
P = []
for i, d in enumerate(gd):
    r = latest(ry, d)
    if r is None:
        continue
    r4 = latest(ry, d - dt.timedelta(days=28))
    r13 = latest(ry, d - dt.timedelta(days=91))
    pc = cot_pct(d)
    P.append(dict(i=i, d=d, px=gold[d], ry=r,
                  dry4=(r - r4) if r4 is not None else None,
                  dry13=(r - r13) if r13 is not None else None,
                  cot=pc))
say(f"weekly panel rows: {len(P)}")

def fwd(i, h):
    """Return from close at index i to close h weeks later."""
    if i + h >= len(gd):
        return None
    return (gold[gd[i+h]] - gold[gd[i]]) / gold[gd[i]]

HOR = (1, 2, 4, 8, 13, 26)

say()
say("=" * 78)
say("H1  REAL YIELD MOMENTUM -> GOLD, ACROSS HORIZONS")
say("=" * 78)
say("Theory: gold is a zero-coupon asset; when the real cost of holding it")
say("FALLS, gold rises. dry = change in real 10y yield. Signal = -sign(dry).")
say(f"{'signal':16s} {'h':>3s} {'n':>5s} {'acc%':>7s} {'mean%':>8s} "
    f"{'t':>7s} {'p(flip)':>8s}")
best = []
for lab, key in [('-sign(d 4w ry)', 'dry4'), ('-sign(d13w ry)', 'dry13')]:
    for h in HOR:
        v, acc = [], []
        for p in P:
            x = p[key]
            if x is None or x == 0:
                continue
            f = fwd(p['i'], h)
            if f is None:
                continue
            s = -np.sign(x)
            v.append(s * f); acc.append(int(np.sign(f) == s))
        if len(v) < 30:
            continue
        m, t, n = tstat(v)
        a = np.mean(acc) * 100
        pv = signflip_null(v)
        say(f"{lab:16s} {h:3d} {n:5d} {a:7.2f} {m*100:+8.3f} {t:+7.2f} {pv:8.4f}")
        best.append((abs(t), lab, h, a, m, t, n, pv))

say()
say("=" * 78)
say("H2  REAL YIELD *LEVEL* REGIME -> GOLD")
say("=" * 78)
say("Not momentum: the level itself, vs its own trailing median (expanding,")
say("no look-ahead). Low real yields = gold-supportive regime.")
say(f"{'signal':16s} {'h':>3s} {'n':>5s} {'acc%':>7s} {'mean%':>8s} "
    f"{'t':>7s} {'p(flip)':>8s}")
for h in HOR:
    v, acc, hist = [], [], []
    for p in P:
        if len(hist) >= 52:
            med = float(np.median(hist))
            s = 1 if p['ry'] < med else -1     # low real yield -> long gold
            f = fwd(p['i'], h)
            if f is not None:
                v.append(s * f); acc.append(int(np.sign(f) == s))
        hist.append(p['ry'])
    if len(v) < 30:
        continue
    m, t, n = tstat(v); a = np.mean(acc) * 100; pv = signflip_null(v)
    say(f"{'ry<med52':16s} {h:3d} {n:5d} {a:7.2f} {m*100:+8.3f} {t:+7.2f} {pv:8.4f}")
    best.append((abs(t), 'ry<med52', h, a, m, t, n, pv))

say()
say("=" * 78)
say("H3  COMBINED STATE: real-yield direction AND positioning")
say("=" * 78)
say("Trade only when the macro driver and the crowd AGREE.")
say(f"{'signal':22s} {'h':>3s} {'n':>5s} {'acc%':>7s} {'mean%':>8s} {'t':>7s}")
for h in HOR:
    v, acc = [], []
    for p in P:
        if p['dry4'] is None or p['cot'] is None or p['dry4'] == 0:
            continue
        s_ry = -np.sign(p['dry4'])
        s_cot = 1 if p['cot'] > .5 else -1
        if s_ry != s_cot:
            continue                       # require agreement
        f = fwd(p['i'], h)
        if f is None:
            continue
        v.append(s_ry * f); acc.append(int(np.sign(f) == s_ry))
    if len(v) < 25:
        continue
    m, t, n = tstat(v); a = np.mean(acc) * 100
    say(f"{'ry AND cot agree':22s} {h:3d} {n:5d} {a:7.2f} {m*100:+8.3f} {t:+7.2f}")
    best.append((abs(t), 'ry+cot agree', h, a, m, t, n, signflip_null(v)))

say()
say("=" * 78)
say("BEST CELL, AND WHAT IT IS WORTH AFTER MULTIPLE-TESTING")
say("=" * 78)
best.sort(reverse=True)
ncell = len(best)
say(f"cells searched: {ncell}   expected max |t| under the null "
    f"~ {np.sqrt(2*np.log(ncell)):.2f}")
for b in best[:6]:
    _, lab, h, a, m, t, n, pv = b
    say(f"  {lab:16s} h={h:2d}w  acc {a:5.2f}%  mean {m*100:+6.3f}%  "
        f"t={t:+5.2f}  n={n}  sign-flip p={pv:.4f}")

say()
say("=" * 78)
say("BUY-AND-HOLD CONTROL (gold rose a lot in this window)")
say("=" * 78)
for h in HOR:
    v = [fwd(p['i'], h) for p in P if fwd(p['i'], h) is not None]
    m, t, n = tstat(v)
    say(f"  h={h:2d}w  long-only mean {m*100:+6.3f}%  t={t:+5.2f}  "
        f"up-rate {np.mean([x>0 for x in v])*100:5.2f}%  n={n}")
say()
say("Any 'directional' signal must beat the long-only column to be real,")
say("because gold went from $1,287 to $3,587 over this sample.")
