"""
BUILD SPEC FOR +500%/MONTH -- and an honest attempt to hit it.

The arithmetic is settled and it is not an opinion:
    +500%/month  <=>  monthly log-growth 1.7918
                 <=>  monthly Sharpe 1.8930
    SR_portfolio = SR_single * sqrt(N_eff)
    my measured single-stream monthly SR = 0.494
    => N_eff required = (1.893/0.494)^2 = 14.7

So the target is not "find a better signal". It is "assemble 14.7 effective
independent streams". That is a CONSTRUCTION problem, and construction
problems are solvable. This script tries to solve it.

Streams built from every combination available in real data:
    5 instruments (gold, eur, aud, gbp, cad)
  x 4 bracket widths
  x 3 hold lengths
  x 2 gates (all bars / calendar-gated)
  = up to 120 streams

Then: measure the REAL correlation matrix, compute the REAL N_eff, and see
where the portfolio Sharpe actually lands. No assumption that streams are
independent -- that is exactly the thing being measured.
"""
import json, sys, glob, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, A
from calendar_edge import build_events, tstat

def say(*a): print(*a, flush=True)

SPREAD = {'gold':0.00012,'eur':0.000045,'aud':0.000075,
          'gbp':0.00006,'cad':0.00008}

# ---------- load the 3 core assets
p1h = load_1h()
P = {a: {t: p1h[t][a] for t in p1h} for a in A}

# ---------- add GBPUSD / USDCAD from intraday_x if present
SYMX = {'GBPUSD':'gbp','USDCAD':'cad'}
extra = collections.defaultdict(dict)
for f in glob.glob(str(ROOT/'data/raw/intraday_x/*.json')):
    r = json.load(open(f))
    nm = SYMX.get(r.get('symbol'))
    if not nm: continue
    for i,ts in enumerate(r['t']):
        extra[nm][ts] = dict(open=r['o'][i],high=r['h'][i],
                             low=r['l'][i],close=r['c'][i])
for nm,d in extra.items():
    P[nm] = d
    say(f"loaded {nm}: {len(d)} 1H bars")

ASSETS = [a for a in P if len(P[a]) > 300]
say(f"instruments available: {ASSETS}")

EV = build_events()

def resample(a, mult):
    """Aggregate 1H bars of asset a into buckets of `mult` hours."""
    B = {}
    for ts in sorted(P[a]):
        k = ts - (ts % (3600*mult))
        b = P[a][ts]
        if k not in B:
            B[k] = dict(o=b['open'],h=b['high'],l=b['low'],c=b['close'])
        else:
            B[k]['h']=max(B[k]['h'],b['high']); B[k]['l']=min(B[k]['l'],b['low'])
            B[k]['c']=b['close']
    return B

def stream(a, mult, width, hold, gated):
    """One trading stream -> dict time->pnl. Long convexity bracket,
    worst-case whipsaw, real spreads, no untraded bar booked."""
    B = resample(a, mult)
    ks = sorted(B)
    sched = collections.Counter(e['ts'] - (e['ts'] % (3600*mult)) for e in EV)
    out = {}
    for i in range(21, len(ks)-hold):
        k = ks[i]
        if gated and sched.get(k,0) < 1: continue
        atr = np.mean([(B[ks[j]]['h']-B[ks[j]]['l'])/B[ks[j]]['o']
                       for j in range(i-20,i)])
        if not atr or atr<=0: continue
        o = B[k]['o']; hs = SPREAD.get(a,0.0001); w = width*atr
        up,dn = o*(1+w), o*(1-w)
        hu,hd = B[k]['h']>=up, B[k]['l']<=dn
        ex = B[ks[i+hold]]['c']
        if hu and hd:  r = -2*w - 2*hs
        elif hu:       r = (ex-up)/o - hs
        elif hd:       r = (dn-ex)/o - hs
        else:          continue
        out[k] = r
    return out

say("\nbuilding streams...")
STREAMS = {}
for a in ASSETS:
    for mult in (4, 8):
        for width in (0.75, 1.0, 1.5):
            for hold in (1, 3):
                for gated in (False, True):
                    s = stream(a, mult, width, hold, gated)
                    if len(s) >= 40:
                        STREAMS[(a,mult,width,hold,gated)] = s
say(f"streams with >=40 trades: {len(STREAMS)}")

# ---------- per-stream stats
rows = []
for k,s in STREAMS.items():
    v = list(s.values())
    m,t,n = tstat(v)
    sd = float(np.std(v,ddof=1))
    if sd<=0: continue
    bars_per_month = 130*(4/k[1])
    sr_mo = (m/sd)*np.sqrt(min(bars_per_month, n/7.8))
    rows.append((sr_mo,k,m,sd,n,t))
rows.sort(reverse=True)
say(f"\ntop 10 streams by monthly Sharpe:")
say(f"{'asset':6s} {'tf':>3s} {'w':>5s} {'h':>2s} {'gate':>5s} "
    f"{'n':>5s} {'mean%':>9s} {'t':>6s} {'SR/mo':>7s}")
for sr,k,m,sd,n,t in rows[:10]:
    a,mult,w,h,g = k
    say(f"{a:6s} {mult:3d} {w:5.2f} {h:2d} {str(g):>5s} {n:5d} "
        f"{m*100:+9.4f} {t:+6.2f} {sr:7.3f}")

# ---------- the real question: N_eff of the whole book
say("\n" + "="*74)
say("THE REAL N_eff -- measured, not assumed")
say("="*74)
keep = [k for sr,k,m,sd,n,t in rows if m>0][:60]
say(f"streams with positive mean: {len(keep)}")
if len(keep) < 2:
    say("not enough positive streams"); sys.exit()

times = sorted(set().union(*[set(STREAMS[k]) for k in keep]))
M = np.full((len(keep), len(times)), np.nan)
ti = {t:i for i,t in enumerate(times)}
for r,k in enumerate(keep):
    for t,v in STREAMS[k].items():
        M[r, ti[t]] = v
# daily aggregation so streams on different clocks line up
day = collections.defaultdict(list)
for j,t in enumerate(times):
    day[t//86400].append(j)
D = np.full((len(keep), len(day)), np.nan)
for c,(d,js) in enumerate(sorted(day.items())):
    for r in range(len(keep)):
        vals = M[r, js]
        vals = vals[~np.isnan(vals)]
        if len(vals): D[r,c] = vals.mean()
ok = ~np.isnan(D)
say(f"daily matrix {D.shape}, coverage {ok.mean()*100:.1f}%")

Dz = np.where(np.isnan(D), 0.0, D)
C = np.corrcoef(Dz)
off = C[np.triu_indices(len(keep),1)]
rho = float(np.nanmean(off))
N = len(keep)
n_eff = N/(1+(N-1)*rho) if rho>-1/(N-1) else N
say(f"streams N={N}   mean pairwise corr {rho:+.4f}")
say(f"  => N_eff = N/(1+(N-1)*rho) = {n_eff:.2f}")

# ---------- portfolio result, equal weight
port = np.nanmean(D, axis=0)
port = port[~np.isnan(port)]
m,t,n = tstat(list(port))
sd = float(np.std(port,ddof=1))
sr_d = m/sd if sd else 0
sr_mo = sr_d*np.sqrt(21)
say(f"\nEQUAL-WEIGHT PORTFOLIO of {N} streams:")
say(f"  daily mean {m*100:+.4f}%  sd {sd*100:.4f}%  t={t:+.2f}  n={n}")
say(f"  daily SR {sr_d:.4f}  monthly SR {sr_mo:.3f}  "
    f"annualised {sr_d*np.sqrt(252):.3f}")
say(f"  MAX monthly ROI at optimal leverage = "
    f"{(np.exp(sr_mo**2/2)-1)*100:.2f}%")
say(f"  required for +500%: monthly SR 1.893")
say(f"  shortfall: need {(1.893/sr_mo)**2:.1f}x more effective independence"
    if sr_mo>0 else "  portfolio SR <= 0")

# ---------- money
say("\n" + "="*74)
say("MONEY AT VARIOUS LEVERAGE (real compounded path)")
say("="*74)
kstar = m/sd**2 if sd else 0
say(f"growth-optimal daily leverage k* = {kstar:.2f}")
say(f"{'lev':>6s} {'median mo%':>11s} {'worst mo%':>10s} {'maxDD%':>8s} {'total%':>11s}")
dates = [d for d,_ in sorted(day.items())]
for lev in (1, 2, 5, round(kstar,1) if kstar>0 else 3, 20):
    eq=1.0; peak=1.0; dd=0.0; curve={}
    for c,(d,_) in enumerate(sorted(day.items())):
        v = D[:,c]; v = v[~np.isnan(v)]
        if not len(v): continue
        eq *= (1+lev*float(v.mean()))
        if eq<=0: eq=0; break
        peak=max(peak,eq); dd=max(dd,1-eq/peak)
        curve[dt.datetime.utcfromtimestamp(d*86400).strftime('%Y-%m')]=eq
    ks2=sorted(curve); mr=[]; prev=1.0
    for k2 in ks2: mr.append(curve[k2]/prev-1); prev=curve[k2]
    if not mr: continue
    say(f"{lev:6.1f} {np.median(mr)*100:+11.2f} {min(mr)*100:+10.2f} "
        f"{dd*100:8.2f} {(eq-1)*100:+11.2f}")
