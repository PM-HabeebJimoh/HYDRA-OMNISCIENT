"""
TWO TESTS I HAVE NEVER ACTUALLY RUN.

TEST 1 -- "IF YOU HAVE 80%, WHERE IS LEVERAGE?"
I found 80.9% accuracy at 36-month horizon on gold, then ASSERTED it could
not be levered monthly because 10x hit ruin. But I only tested NAKED
leverage. I never tested VOLATILITY TARGETING -- the standard technique
that de-levers into turbulence and re-levers into calm. That is exactly
what prevents the ruin path. Testing it now on 23.5 years of real data.

TEST 2 -- IS THERE A HIGH-ACCURACY POCKET?
I tested confidence-filtering on an ML ensemble (it went backwards). I never
ran an exhaustive CONDITIONAL search: are there specific, rare, mechanically
defined states where next-bar accuracy is 70-80%? Searching every
combination of regime conditions, with proper multiple-testing control.

No conclusions until both have run.
"""
import json, sys, glob, collections, itertools, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events, tstat, signflip_null

def say(*a): print(*a, flush=True)

# =====================================================================
say("="*76)
say("TEST 1: VOL-TARGETED LEVERAGE ON THE 80.9% DRIFT EDGE (23.5 YEARS)")
say("="*76)

D = json.load(open(ROOT/'data/raw/long/monthly.json'))
g = D['gold']; ms = sorted(g); G = np.array([g[k] for k in ms])
r = np.diff(G)/G[:-1]
say(f"real monthly gold returns: n={len(r)}  {ms[0]} .. {ms[-1]}")
say(f"mean {r.mean()*100:+.3f}%  sd {r.std()*100:.3f}%  "
    f"monthly SR {r.mean()/r.std():.4f}")

def run(lev_fn, label):
    eq, peak, dd, mo, ruin = 1.0, 1.0, 0.0, [], False
    hist = []
    for i, x in enumerate(r):
        k = lev_fn(hist, i)
        step = 1 + k*x
        if step <= 0:
            ruin = True; eq = 0.0; mo.append(-1.0); break
        eq *= step; mo.append(k*x)
        peak = max(peak, eq); dd = max(dd, 1-eq/peak)
        hist.append(x)
    yrs = len(r)/12
    cagr = (eq**(1/yrs)-1)*100 if eq > 0 else -100
    wr = np.mean([m > 0 for m in mo])*100
    return dict(label=label, eq=eq, cagr=cagr, dd=dd*100,
                med=np.median(mo)*100, worst=min(mo)*100, wr=wr, ruin=ruin)

TARGET_VOL = None
def voltarget(tv, cap):
    def f(hist, i):
        if len(hist) < 12:
            return 1.0
        rv = float(np.std(hist[-12:]))
        if rv <= 0: return cap
        return float(min(tv/rv, cap))
    return f

say(f"\n{'strategy':34s} {'WR%':>6s} {'medMo%':>8s} {'worstMo%':>9s} "
    f"{'maxDD%':>8s} {'CAGR%':>8s} {'final x':>10s}")
res = []
for k in (1, 3, 5, 8, 10, 15):
    o = run(lambda h, i, k=k: k, f"fixed {k}x")
    res.append(o)
    say(f"{o['label']:34s} {o['wr']:6.1f} {o['med']:+8.2f} {o['worst']:+9.2f} "
        f"{o['dd']:8.1f} {o['cagr']:8.2f} "
        f"{'RUIN' if o['ruin'] else f'{o[chr(101)+chr(113)]:10.1f}'}")
for tv, cap in [(0.04, 10), (0.04, 20), (0.06, 20), (0.06, 40), (0.08, 40)]:
    o = run(voltarget(tv, cap), f"vol-target {tv*100:.0f}% cap {cap}x")
    res.append(o)
    say(f"{o['label']:34s} {o['wr']:6.1f} {o['med']:+8.2f} {o['worst']:+9.2f} "
        f"{o['dd']:8.1f} {o['cagr']:8.2f} "
        f"{'RUIN' if o['ruin'] else f'{o[chr(101)+chr(113)]:10.1f}'}")

best = max([x for x in res if not x['ruin']], key=lambda x: x['cagr'])
say(f"\n  BEST: {best['label']}  CAGR {best['cagr']:.2f}%  "
    f"median month {best['med']:+.2f}%  maxDD {best['dd']:.1f}%")
say(f"  Does vol targeting unlock 500%/month? "
    f"{'YES' if best['med'] >= 500 else 'NO -- median month is '+f'{best[chr(109)+chr(101)+chr(100)]:+.2f}%'}")

# =====================================================================
say()
say("="*76)
say("TEST 2: EXHAUSTIVE CONDITIONAL SEARCH FOR A HIGH-ACCURACY POCKET")
say("="*76)

p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4)
EV = build_events()
sched = collections.Counter(e['ts']-(e['ts']%14400) for e in EV)
MAC = {}
for f in glob.glob(str(ROOT/'data/raw/macro/*.json')):
    d = json.load(open(f))
    MAC[Path(f).stem] = {dt.date.fromisoformat(x): v
                         for x, v in zip(d['dates'], d['v']) if v is not None}
MS = {k: sorted(MAC.get(k, {})) for k in MAC}
def mac(k, d):
    best = None
    for x in MS.get(k, []):
        if x < d: best = MAC[k][x]
        else: break
    return best

S = {}
for a in A:
    out, pc = [], None
    for t in b4:
        x = p4[t][a]
        out.append((t, x['open'], x['high'], x['low'], x['close'],
                    pc if pc else x['open']))
        pc = x['close']
    S[a] = out
N = len(b4)

# build boolean condition set per bar, per asset
def conds(a, i):
    q = S[a]; t = q[i][0]; d = dt.datetime.utcfromtimestamp(t).date()
    _, o, h, l, c, pc = q[i]
    rng = max(h-l, 1e-12)
    rr = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i)]
    atr = np.mean(rr); atr5 = np.mean(rr[-5:])
    body = (c-o)/o
    clv = (c-l)/rng
    strk = sum(np.sign((q[j][4]-q[j][1])) for j in range(i-3, i))
    vix = mac('VIX', d) or 0
    gvz = mac('GVZ', d) or 0
    hh = dt.datetime.utcfromtimestamp(t).hour
    return {
        'up_bar': body > 0,
        'big_body': abs(body) > atr*0.5,
        'high_clv': clv > 0.7,
        'low_clv': clv < 0.3,
        'streak3_up': strk == 3,
        'streak3_dn': strk == -3,
        'vol_expand': atr5 > atr*1.2,
        'vol_quiet': atr5 < atr*0.8,
        'event_bar': sched.get(t, 0) >= 1,
        'event_next': sched.get(t+14400, 0) >= 1,
        'vix_high': vix > 20,
        'vix_low': 0 < vix < 15,
        'gvz_high': gvz > 25,
        'london': 7 <= hh < 13,
        'ny': 13 <= hh < 20,
        'asia': hh < 7 or hh >= 20,
    }

say("building condition matrix...")
ROWS = []
for a in A:
    q = S[a]
    for i in range(25, N-1):
        cd = conds(a, i)
        nx = q[i+1]
        ROWS.append((a, i, cd, 1 if nx[4] > nx[1] else 0))
say(f"rows: {len(ROWS)}")
KEYS = sorted(ROWS[0][2])

say("\nsearching all 1-, 2- and 3-condition combinations...")
found = []
for k in (1, 2, 3):
    for combo in itertools.combinations(KEYS, k):
        for signs in itertools.product([True, False], repeat=k):
            sel = [row for row in ROWS
                   if all(row[2][c] == s for c, s in zip(combo, signs))]
            if len(sel) < 60:
                continue
            y = np.array([row[3] for row in sel])
            acc = max(y.mean(), 1-y.mean())*100
            n = len(y)
            z = (acc-50)/(np.sqrt(0.25/n)*100)
            found.append((acc, z, n, combo, signs))
found.sort(reverse=True)
ncell = len(found)
say(f"cells tested: {ncell}")
say(f"expected max |z| under pure noise: {np.sqrt(2*np.log(max(ncell,2))):.2f}")
say(f"\n{'acc%':>7s} {'z':>7s} {'n':>6s}  condition")
for acc, z, n, combo, signs in found[:12]:
    desc = " AND ".join(f"{'' if s else 'NOT '}{c}" for c, s in zip(combo, signs))
    say(f"{acc:7.2f} {z:+7.2f} {n:6d}  {desc}")

if found:
    acc, z, n, combo, signs = found[0]
    say(f"\n  BEST POCKET: {acc:.2f}% on n={n}")
    say(f"  z = {z:+.2f} vs noise expectation "
        f"{np.sqrt(2*np.log(max(ncell,2))):.2f}")
    if z > np.sqrt(2*np.log(max(ncell, 2))):
        say("  -> EXCEEDS the multiple-testing threshold. Worth validating.")
    else:
        say("  -> BELOW the multiple-testing threshold. This is noise.")
    say(f"  Is any pocket >=80% with n>=60? "
        f"{'YES' if acc >= 80 else 'NO -- best is '+f'{acc:.2f}%'}")
