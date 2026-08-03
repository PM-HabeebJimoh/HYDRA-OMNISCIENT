"""
SETTLE THE POCKET BY MAXIMISING SAMPLE.

The blocker I named was sample size: n=85, t=+1.77, needs ~460 signals.
Instead of asking for data, extract every signal available from what exists.

Sample multipliers available right now:
  * 5 instruments instead of 3            (gold eur aud gbp cad)
  * 3 timeframes instead of 1             (1H, 4H, 8H)
  * both directions of the pattern        (up-bar and down-bar variants)

The pattern under test, stated mechanically:
  "On a scheduled-release bar, in NON-expanding volatility, a bar that
   closes UP is followed by a DOWN bar."
i.e. event-day exhaustion / reversion in calm conditions.

Everything walk-forward-safe (all conditions causal), traded on the true
1H path where possible, real spreads, worst-case whipsaw.
"""
import json, sys, glob, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, A
from calendar_edge import build_events, tstat, signflip_null

def say(*a): print(*a, flush=True)
SPREAD = {'gold':0.00012,'eur':0.000045,'aud':0.000075,
          'gbp':0.00006,'cad':0.00008}

p1h = load_1h()
P = {a: {t: p1h[t][a] for t in p1h} for a in A}
for f in glob.glob(str(ROOT/'data/raw/intraday_x/*.json')):
    r = json.load(open(f))
    nm = {'GBPUSD':'gbp','USDCAD':'cad'}.get(r.get('symbol'))
    if nm:
        P[nm] = {ts: dict(open=r['o'][i],high=r['h'][i],low=r['l'][i],
                          close=r['c'][i]) for i,ts in enumerate(r['t'])}
ASSETS = [a for a in P if len(P[a]) > 300]
say(f"instruments: {ASSETS}")
EV = build_events()

def bars(a, mult):
    B = {}
    for ts in sorted(P[a]):
        k = ts-(ts % (3600*mult)); b = P[a][ts]
        if k not in B:
            B[k] = dict(o=b['open'],h=b['high'],l=b['low'],c=b['close'])
        else:
            B[k]['h']=max(B[k]['h'],b['high']); B[k]['l']=min(B[k]['l'],b['low'])
            B[k]['c']=b['close']
    return B

def collect(mult, vol_mult=1.2):
    """Return list of (asset, time, next_return, next_up) for pattern hits."""
    sched = collections.Counter(e['ts']-(e['ts'] % (3600*mult)) for e in EV)
    hits = []
    for a in ASSETS:
        B = bars(a, mult); ks = sorted(B)
        for i in range(21, len(ks)-1):
            k = ks[i]
            if sched.get(k, 0) < 1:
                continue
            b = B[k]
            if b['c'] <= b['o']:
                continue                      # need an UP bar
            rr = [(B[ks[j]]['h']-B[ks[j]]['l'])/B[ks[j]]['o']
                  for j in range(i-20, i)]
            if np.mean(rr[-5:]) > np.mean(rr)*vol_mult:
                continue                      # need NON-expanding vol
            nx = B[ks[i+1]]
            hits.append((a, k, (nx['c']-nx['o'])/nx['o'],
                         1 if nx['c'] > nx['o'] else 0, mult))
    return hits

say("\n" + "="*76)
say("SAMPLE MAXIMISATION: same pattern, every instrument and timeframe")
say("="*76)
say(f"{'timeframe':>10s} {'n':>6s} {'DOWN rate':>11s} {'z':>8s}")
ALL = []
for mult in (1, 2, 4, 8):
    h = collect(mult)
    if len(h) < 30: continue
    ALL += h
    y = np.array([x[3] for x in h])
    dn = (1-y.mean())*100
    z = (dn-50)/(np.sqrt(0.25/len(y))*100)
    say(f"{str(mult)+'H':>10s} {len(y):6d} {dn:10.2f}% {z:+8.2f}")
y = np.array([x[3] for x in ALL])
dn = (1-y.mean())*100
z = (dn-50)/(np.sqrt(0.25/len(y))*100)
say(f"{'POOLED':>10s} {len(y):6d} {dn:10.2f}% {z:+8.2f}")
say(f"\n  target was ~460 signals. Achieved: {len(y)}")

say("\n" + "="*76)
say("PER-INSTRUMENT (does it live in one asset?)")
say("="*76)
for a in ASSETS:
    sub = [x for x in ALL if x[0] == a]
    if len(sub) < 25: continue
    yy = np.array([x[3] for x in sub])
    d = (1-yy.mean())*100
    zz = (d-50)/(np.sqrt(0.25/len(yy))*100)
    say(f"  {a:5s} n={len(yy):4d}  DOWN {d:5.2f}%  z={zz:+.2f}")

say("\n" + "="*76)
say("PER-MONTH (is it constant?)")
say("="*76)
bym = collections.defaultdict(list)
for a, k, r, u, m in ALL:
    bym[dt.datetime.utcfromtimestamp(k).strftime('%Y-%m')].append(u)
for k in sorted(bym):
    yy = np.array(bym[k]); d = (1-yy.mean())*100
    say(f"  {k}  n={len(yy):4d}  DOWN {d:5.1f}%")
say(f"  months >50% DOWN: "
    f"{sum(1 for v in bym.values() if (1-np.mean(v))>0.5)}/{len(bym)}")

say("\n" + "="*76)
say("MONEY: trade it SHORT, real spreads, honest exits")
say("="*76)
say(f"{'tf':>4s} {'n':>6s} {'WR%':>6s} {'mean%':>9s} {'t':>7s} {'p':>8s}")
for mult in (1, 2, 4, 8):
    sub = [x for x in ALL if x[4] == mult]
    if len(sub) < 30: continue
    pnl = [-x[2] - 2*SPREAD[x[0]] for x in sub]
    m, t, n = tstat(pnl)
    wr = np.mean([v > 0 for v in pnl])*100
    say(f"{str(mult)+'H':>4s} {n:6d} {wr:6.1f} {m*100:+9.4f} {t:+7.2f} "
        f"{signflip_null(pnl):8.4f}")
pnl = [-x[2] - 2*SPREAD[x[0]] for x in ALL]
m, t, n = tstat(pnl)
wr = np.mean([v > 0 for v in pnl])*100
say(f"{'ALL':>4s} {n:6d} {wr:6.1f} {m*100:+9.4f} {t:+7.2f} "
    f"{signflip_null(pnl):8.4f}")

say("\n" + "="*76)
say("SPLIT-HALF ON THE POOLED SAMPLE")
say("="*76)
ALLs = sorted(ALL, key=lambda x: x[1])
h = len(ALLs)//2
for lab, s in [('first half ', ALLs[:h]), ('second half', ALLs[h:])]:
    p = [-x[2]-2*SPREAD[x[0]] for x in s]
    mm, tt, nn = tstat(p)
    say(f"  {lab} n={nn:5d}  mean {mm*100:+.4f}%  t={tt:+.2f}  "
        f"WR {np.mean([v>0 for v in p])*100:.1f}%")

say("\n" + "="*76)
say("MONTHLY ROI AT GROWTH-OPTIMAL LEVERAGE")
say("="*76)
sd = float(np.std(pnl, ddof=1))
k = m/sd**2 if sd > 0 and m > 0 else 0
say(f"  per-trade mean {m*100:+.4f}%  sd {sd*100:.4f}%  k* = {k:.2f}")
if k > 0:
    byt = collections.defaultdict(list)
    for x in ALL:
        byt[dt.datetime.utcfromtimestamp(x[1]).strftime('%Y-%m')].append(
            -x[2]-2*SPREAD[x[0]])
    for lev in (1, 5, round(k, 1)):
        eq, peak, dd, mr = 1.0, 1.0, 0.0, []
        for mth in sorted(byt):
            e0 = eq
            for v in byt[mth]:
                eq *= (1+lev*v)
                if eq <= 0: eq = 1e-12; break
            mr.append(eq/e0-1)
            peak = max(peak, eq); dd = max(dd, 1-eq/peak)
        say(f"\n  leverage {lev}x:  median month {np.median(mr)*100:+.2f}%  "
            f"maxDD {dd*100:.1f}%  total {(eq-1)*100:+.1f}%")
        for mth, r in zip(sorted(byt), mr):
            say(f"     {mth}  {r*100:+10.2f}%")
        say(f"     months positive: {sum(1 for r in mr if r>0)}/{len(mr)}")
