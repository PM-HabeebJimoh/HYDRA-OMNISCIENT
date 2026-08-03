"""
ROI ONLY. NO WR CONSTRAINT. NO DD CONSTRAINT.
GOAL: >500% EVERY MONTH.

If drawdown does not matter, leverage is the only question. So find the
MAXIMUM leverage each configuration can take, and see what it produces.

The binding constraint on leverage is not drawdown -- it is RUIN:
    at leverage k, a single trade losing L wipes you out if k*L >= 1
    => k_max = 1 / |worst single trade|

That is a hard physical limit, not a preference. Past it, equity hits zero
and every subsequent month is -100%.

So for every config:
    1. find worst single trade -> k_max
    2. run at 0.5*k_max, 0.9*k_max, 0.99*k_max
    3. report EVERY month's ROI
    4. check: is the MINIMUM month above +500%?
"""
import json, sys, glob, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'scripts')); sys.path.insert(0, str(ROOT/'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events, tstat

def say(*a): print(*a, flush=True)
SPREAD = {'gold':0.00012,'eur':0.000045,'aud':0.000075,'gbp':0.00006,'cad':0.00008}

p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4)
EV = build_events()
sched4 = collections.Counter(e['ts']-(e['ts']%14400) for e in EV)
S = {}
for a in A:
    out, pc = [], None
    for t in b4:
        x = p4[t][a]
        out.append((t,x['open'],x['high'],x['low'],x['close'],pc if pc else x['open']))
        pc = x['close']
    S[a] = out
N = len(b4)

def bracket(gate, width=1.0, hold=3):
    out = []
    for a in A:
        q = S[a]
        for i in range(21, N-hold):
            if gate and sched4.get(q[i][0],0) < 1: continue
            atr = np.mean([(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i)])
            if not atr: continue
            o, hs = q[i][1], SPREAD[a]; w = width*atr
            up, dn = o*(1+w), o*(1-w)
            hu, hd = q[i][2]>=up, q[i][3]<=dn
            if hu and hd: r = -2*w-2*hs
            elif hu: r = (q[i+hold][4]-up)/o-hs
            elif hd: r = (dn-q[i+hold][4])/o-hs
            else: continue
            out.append((q[i][0], a, r))
    return sorted(out)

def monthly(T, lev):
    """Compound trade by trade. Concurrent trades share equity equally."""
    byt = collections.defaultdict(list)
    for t,a,r in T: byt[t].append(r)
    eq = 1.0; curve = {}
    for t in sorted(byt):
        step = 1 + lev*float(np.mean(byt[t]))
        if step <= 0:
            eq = 0.0
            curve[dt.datetime.utcfromtimestamp(t).strftime('%Y-%m')] = 0.0
            break
        eq *= step
        curve[dt.datetime.utcfromtimestamp(t).strftime('%Y-%m')] = eq
    ks = sorted(curve); mr = []; prev = 1.0
    for k in ks:
        mr.append(curve[k]/prev - 1); prev = curve[k] if curve[k] > 0 else 1e-18
    return ks, mr, eq

say("="*76)
say("STEP 1: FIND CONFIGS WHERE EVERY MONTH IS POSITIVE UNLEVERED")
say("="*76)
say("Leverage CANNOT turn a negative month positive. It multiplies.")
say("So a config with any negative month can never give >500% every month.\n")
say(f"{'config':28s} {'n':>5s} {'months+':>8s} {'worst mo%':>10s} "
    f"{'worst trade%':>13s} {'k_max':>8s}")
CONF = {}
for lab, gate, w, h in [("all bars w1.0 h3", False,1.0,3),
                        ("all bars w0.75 h3", False,0.75,3),
                        ("all bars w1.5 h3", False,1.5,3),
                        ("CALENDAR w1.0 h3", True,1.0,3),
                        ("CALENDAR w0.75 h3", True,0.75,3),
                        ("CALENDAR w1.5 h3", True,1.5,3),
                        ("CALENDAR w1.0 h1", True,1.0,1)]:
    T = bracket(gate, w, h)
    if len(T) < 30: continue
    ks, mr, eq = monthly(T, 1.0)
    worst_trade = min(r for _,_,r in T)
    kmax = 1/abs(worst_trade) if worst_trade < 0 else 999
    npos = sum(1 for r in mr if r > 0)
    CONF[lab] = (T, mr, ks, kmax)
    say(f"{lab:28s} {len(T):5d} {npos:>4d}/{len(mr):<3d} "
        f"{min(mr)*100:+10.3f} {worst_trade*100:+13.3f} {kmax:8.1f}")

say()
say("="*76)
say("STEP 2: THE CONFIGS WITH 8/8 POSITIVE MONTHS -- PUSH LEVERAGE")
say("="*76)
winners = [(l,v) for l,v in CONF.items() if all(r > 0 for r in v[1])]
if not winners:
    say("  NONE. Every config has at least one negative month.")
else:
    for lab,(T,mr,ks,kmax) in winners:
        say(f"\n  --- {lab}   k_max (ruin limit) = {kmax:.1f}x")
        say(f"  {'lev':>8s} " + " ".join(f"{k[-2:]:>9s}" for k in ks) +
            f" {'MIN mo%':>10s}")
        for frac in (0.25, 0.5, 0.75, 0.9, 0.99):
            lev = kmax*frac
            _, m2, _ = monthly(T, lev)
            if len(m2) != len(ks): m2 = m2 + [-1.0]*(len(ks)-len(m2))
            row = f"  {lev:8.1f} " + " ".join(
                f"{r*100:9.1f}" if abs(r) < 1e6 else f"{r:9.1e}" for r in m2)
            say(row + f" {min(m2)*100:10.1f}")
        # exact leverage needed for the WEAKEST month to reach +500%
        say(f"\n  weakest month unlevered: {min(mr)*100:+.4f}%")
        lo, hi = 1.0, kmax
        best = None
        for _ in range(60):
            mid = (lo+hi)/2
            _, m2, _ = monthly(T, mid)
            if len(m2) < len(ks) or min(m2) <= 5.0:
                hi = mid
            else:
                lo = mid; best = mid
        if best:
            _, m2, _ = monthly(T, best)
            say(f"  LEVERAGE ACHIEVING >500% EVERY MONTH: {best:.2f}x")
            for k, r in zip(ks, m2):
                say(f"     {k}  {r*100:+12.2f}%")
        else:
            _, m2, _ = monthly(T, kmax*0.99)
            say(f"  At 99% of ruin leverage ({kmax*0.99:.1f}x) the weakest "
                f"month is {min(m2)*100:+.2f}%")
            say(f"  >500% every month is NOT reachable by leverage alone.")

say()
say("="*76)
say("STEP 3: WHY -- THE ARITHMETIC OF LEVERAGING A COMPOUNDED MONTH")
say("="*76)
say("""A month is a PRODUCT of trades, not a sum:
      month(k) = PROD_i (1 + k*r_i)
Even when the month is net positive, it contains losing trades. Raising k
grows winners linearly but drives (1 + k*r_i) toward zero for every loser.
Past k = 1/|worst loss| a single trade zeroes the account.

So the achievable monthly return is capped by the WORST TRADE IN THAT MONTH,
not by the month's average. That is the real answer to 'where is leverage'.""")
for lab,(T,mr,ks,kmax) in list(CONF.items())[:3]:
    byt = collections.defaultdict(list)
    for t,a,r in T: byt[t].append(r)
    bym = collections.defaultdict(list)
    for t in byt: bym[dt.datetime.utcfromtimestamp(t).strftime('%Y-%m')].append(
        float(np.mean(byt[t])))
    say(f"\n  {lab}")
    for mth in sorted(bym):
        v = bym[mth]; wt = min(v)
        km = 1/abs(wt) if wt < 0 else 999
        best_r = np.prod([1+km*0.99*x for x in v]) - 1
        say(f"     {mth}  worst bar {wt*100:+7.3f}%  k_max {km:6.1f}x  "
            f"max month {best_r*100:+10.1f}%")
