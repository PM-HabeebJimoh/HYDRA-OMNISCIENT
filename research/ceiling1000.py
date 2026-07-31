#!/usr/bin/env python3
"""WHY does live-correct ROI cap out below 1000%? Find the exact ceiling.
Key fact: equity compounds multiplicatively. Raising leverage raises BOTH the
win and the loss on every bar. Past a point, extra leverage LOWERS final equity
and eventually guarantees ruin. That optimum is the ceiling."""
import sys, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)
def daily(p):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%86400)
        for a in A:
            d=p[t][a]
            if a not in B[b]: B[b][a]=dict(d)
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
PAN={'DAILY':daily(p1),'4H':p4,'1H':p1}

def bar_returns(panel,lo,hi,flip,stop=0.01):
    """Per-bar BASKET return per unit of notional/equity (k=1). Live-correct."""
    keys=sorted(panel); out=[]
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s=panel[sk]
        dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
        if not (dn or up): continue
        side=(-1 if dn else 1)*(-1 if flip else 1)
        legs=[]
        for a in A:
            b=panel[ek][a]; e=b['open']
            if side<0:
                sp=e*(1+stop); ex=sp if (stop and b['high']>=sp) else b['close']; r=(e-ex)/e
            else:
                sp=e*(1-stop); ex=sp if (stop and b['low']<=sp) else b['close']; r=(ex-e)/e
            legs.append(r)
        out.append(np.mean(legs))
    return np.array(out)

MON=[('Dec25',1764547200,1767225600),('Jan26',1767225600,1769904000),('Feb26',1769904000,1772323200),
     ('Mar26',1772323200,1775001600),('Apr26',1775001600,1777593600),('May26',1777593600,1780272000),
     ('Jun26',1780272000,1782864000),('Jul26',1782864000,1785542400)]

print("="*100)
print("MAXIMUM ACHIEVABLE ROI PER MONTH/TF — leverage optimised to the exact peak")
print("(k = notional/equity summed across the 3 legs; 500x at 20% risk = k 100)")
print("="*100)
print(f"{'month':>6} {'TF':>6} {'dir':>5} {'n':>4} {'best k':>8} {'equiv lev':>10} {'MAX ROI':>14} {'maxDD':>9}")
rows=[]
for nm,lo,hi in MON:
    for tf in ('DAILY','4H','1H'):
        best=None
        for flip in (False,True):
            for stop in (0.0,0.005,0.01,0.02):
                r=bar_returns(PAN[tf],lo,hi,flip,stop)
                if len(r)==0: continue
                for k in np.arange(0.5,300,0.5):
                    g=1+r*k
                    if (g<=0).any(): break
                    eq=np.cumprod(g); pk=np.maximum.accumulate(eq)
                    ret=(eq[-1]-1)*100
                    if best is None or ret>best[0]:
                        best=(ret,flip,k,stop,((eq-pk)/pk).min()*100,len(r))
        if best:
            ret,flip,k,stop,dd,n=best
            rows.append((nm,tf,ret))
            print(f"{nm:>6} {tf:>6} {'FADE' if flip else 'FOLL':>5} {n:4d} {k:8.1f} {k/3*5:9.0f}x {ret:13,.2f}% {dd:8.2f}%")
mx=max(r[2] for r in rows)
print()
print(f"HIGHEST ROI ACHIEVABLE ANYWHERE, any month/TF/direction/stop, leverage tuned to the")
print(f"single best value with full hindsight:  {mx:,.2f}%")
print(f"TARGET: 1000%   ->  {'ACHIEVED' if mx>1000 else 'NOT ACHIEVABLE on this data'}")
print()
print("WHY there is a ceiling (this is arithmetic, not an opinion):")
print("  Equity compounds: E = prod(1 + k*r_i). Raising k scales EVERY r_i, wins and losses alike.")
print("  d/dk of log-equity = sum( r_i / (1 + k*r_i) ). This is strictly decreasing in k.")
print("  It crosses zero at one point - the growth optimum. Beyond it more leverage LOWERS")
print("  final equity, and once k*|worst r_i| >= 1 the account is wiped in a single bar.")
print("  So ROI is bounded by the edge in r, not by the leverage you are willing to use.")
