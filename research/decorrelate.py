"""
THE ONLY REMAINING BLOCKER: rho <= 0.068

Everything reduces to this. N_eff -> 1/rho as N grows, so:
    rho 0.436 (measured) -> ceiling  22%/month
    rho 0.068 (required) -> ceiling 500%/month

My 15 streams are correlated at 0.436 because they are all the SAME
strategy on the SAME USD-quoted instruments. The fix is streams that do
not share a driver.

This script builds STRUCTURALLY DIFFERENT strategy families and measures
the real cross-family correlation:

  F1 CONVEXITY   long bracket   (profits from large moves)
  F2 REVERSION   fade extremes  (profits from small moves)  <- inverse of F1
  F3 MOMENTUM    follow the bar (profits from continuation)
  F4 CARRY-PROXY hold the trend (profits from drift)
  F5 CROSS-SEC   long/short pairs (dollar-neutral by construction)

F1 and F2 are mechanically opposed -- if anything can be negatively
correlated, it is those. That is the test.
"""
import json, sys, glob, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, A
from calendar_edge import tstat

def say(*a): print(*a, flush=True)
SPREAD = {'gold':0.00012,'eur':0.000045,'aud':0.000075,'gbp':0.00006,'cad':0.00008}

p1h = load_1h()
P = {a: {t: p1h[t][a] for t in p1h} for a in A}
for f in glob.glob(str(ROOT/'data/raw/intraday_x/*.json')):
    r = json.load(open(f))
    nm = {'GBPUSD':'gbp','USDCAD':'cad'}.get(r.get('symbol'))
    if nm:
        P[nm] = {ts: dict(open=r['o'][i],high=r['h'][i],low=r['l'][i],
                          close=r['c'][i]) for i,ts in enumerate(r['t'])}
ASSETS = [a for a in P if len(P[a])>300]

def bars(a, mult=4):
    B={}
    for ts in sorted(P[a]):
        k=ts-(ts%(3600*mult)); b=P[a][ts]
        if k not in B: B[k]=dict(o=b['open'],h=b['high'],l=b['low'],c=b['close'])
        else:
            B[k]['h']=max(B[k]['h'],b['high']); B[k]['l']=min(B[k]['l'],b['low'])
            B[k]['c']=b['close']
    return B

def fam(a, kind, mult=4, hold=1):
    """One strategy family on one asset -> {time: pnl}."""
    B=bars(a,mult); ks=sorted(B); out={}; hs=SPREAD.get(a,1e-4)
    for i in range(21,len(ks)-hold):
        k=ks[i]
        atr=np.mean([(B[ks[j]]['h']-B[ks[j]]['l'])/B[ks[j]]['o'] for j in range(i-20,i)])
        if not atr or atr<=0: continue
        o=B[k]['o']; hi=B[k]['h']; lo=B[k]['l']; c=B[k]['c']
        ex=B[ks[i+hold]]['c']
        prev=B[ks[i-1]]
        if kind=='convex':
            w=1.0*atr; up,dn=o*(1+w),o*(1-w)
            hu,hd=hi>=up,lo<=dn
            if hu and hd: r=-2*w-2*hs
            elif hu: r=(ex-up)/o-hs
            elif hd: r=(dn-ex)/o-hs
            else: continue
        elif kind=='revert':
            w=1.0*atr; up,dn=o*(1+w),o*(1-w)
            hu,hd=hi>=up,lo<=dn
            st=2.0*w
            if hi>=o*(1+st) or lo<=o*(1-st): r=-st-hs
            elif hu and hd: r=2*w-2*hs
            elif hu: r=(up-ex)/o-hs
            elif hd: r=(ex-dn)/o-hs
            else: continue
        elif kind=='moment':
            s=np.sign(prev['c']-prev['o'])
            if s==0: continue
            r=s*(ex-o)/o-hs
        elif kind=='trend':
            ma=np.mean([B[ks[j]]['c'] for j in range(i-20,i)])
            s=1 if o>ma else -1
            r=s*(ex-o)/o-hs
        else: continue
        out[k]=r
    return out

say("building strategy families...")
S={}
for a in ASSETS:
    for kind in ('convex','revert','moment','trend'):
        for mult in (4,8):
            s=fam(a,kind,mult)
            if len(s)>=40: S[(a,kind,mult)]=s
say(f"streams: {len(S)}")

# cross-sectional (dollar-neutral) streams
pairs=[('gold','eur'),('gold','aud'),('eur','aud'),('gbp','cad')]
for x,y in pairs:
    if x not in P or y not in P: continue
    Bx,By=bars(x),bars(y); ks=sorted(set(Bx)&set(By)); out={}
    for i in range(21,len(ks)-1):
        k=ks[i]
        mx=np.mean([(Bx[ks[j]]['c']-Bx[ks[j]]['o'])/Bx[ks[j]]['o'] for j in range(i-5,i)])
        my=np.mean([(By[ks[j]]['c']-By[ks[j]]['o'])/By[ks[j]]['o'] for j in range(i-5,i)])
        s=np.sign(mx-my)
        if s==0: continue
        nx,ny=Bx[ks[i+1]],By[ks[i+1]]
        rx=(nx['c']-nx['o'])/nx['o']; ry=(ny['c']-ny['o'])/ny['o']
        out[k]=s*(rx-ry)-SPREAD.get(x,1e-4)-SPREAD.get(y,1e-4)
    if len(out)>=40: S[(f'{x}/{y}','xsec',4)]=out
say(f"streams incl cross-sectional: {len(S)}")

# ---- daily matrix
times=sorted(set().union(*[set(v) for v in S.values()]))
keys=list(S)
day=collections.defaultdict(list)
for t in times: day[t//86400].append(t)
dl=sorted(day)
D=np.full((len(keys),len(dl)),np.nan)
for r,k in enumerate(keys):
    for c,d in enumerate(dl):
        vals=[S[k][t] for t in day[d] if t in S[k]]
        if vals: D[r,c]=float(np.mean(vals))

say("\n"+"="*74)
say("CORRELATION *BETWEEN* STRATEGY FAMILIES -- the decisive table")
say("="*74)
fams=sorted(set(k[1] for k in keys))
Dz=np.where(np.isnan(D),0.0,D)
C=np.corrcoef(Dz)
say(f"{'':10s}"+"".join(f"{f:>10s}" for f in fams))
for f1 in fams:
    i1=[i for i,k in enumerate(keys) if k[1]==f1]
    row=f"{f1:10s}"
    for f2 in fams:
        i2=[i for i,k in enumerate(keys) if k[1]==f2]
        vals=[C[a,b] for a in i1 for b in i2 if a!=b]
        row+=f"{np.mean(vals):10.3f}" if vals else f"{'-':>10s}"
    say(row)

say("\n"+"="*74)
say("PORTFOLIO OF ALL FAMILIES -- does mixing break the wall?")
say("="*74)
pos=[i for i,k in enumerate(keys)
     if np.nanmean(D[i])>0 and np.sum(~np.isnan(D[i]))>=30]
say(f"positive streams: {len(pos)} of {len(keys)}")
if len(pos)>=2:
    Cp=C[np.ix_(pos,pos)]
    off=Cp[np.triu_indices(len(pos),1)]
    rho=float(np.mean(off)); N=len(pos)
    n_eff=N/(1+(N-1)*rho)
    say(f"mean pairwise rho = {rho:+.4f}   N={N}   N_eff={n_eff:.2f}")
    say(f"ceiling as N->inf: N_eff = 1/rho = {1/rho if rho>0 else float('inf'):.1f}")
    port=np.nanmean(D[pos],axis=0); port=port[~np.isnan(port)]
    m=float(np.mean(port)); sd=float(np.std(port,ddof=1))
    sr_mo=(m/sd)*np.sqrt(21) if sd else 0
    say(f"\nportfolio daily mean {m*100:+.4f}%  sd {sd*100:.4f}%")
    say(f"monthly SR {sr_mo:.3f}  ->  max monthly ROI "
        f"{(np.exp(sr_mo**2/2)-1)*100:.2f}%")
    say(f"required monthly SR for +500%: 1.893")
    say(f"required rho for +500%: 0.068   |   measured rho: {rho:.4f}")
