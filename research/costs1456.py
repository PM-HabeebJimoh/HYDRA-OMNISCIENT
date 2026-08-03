#!/usr/bin/env python3
"""Final gate: apply REAL EURUSD trading costs to the 1H fade.
1834 round trips at k=71.5 is enormous turnover - cost is the decisive test."""
import sys, datetime
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h
A=('gold','eur','aud'); LO,HI=1764547200,1785542400
p1=load_1h()
def single(panel,lo,hi,asset,flip,stop):
    keys=sorted(panel); out=[]
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s=panel[sk]
        dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
        if not (dn or up): continue
        side=(-1 if dn else 1)*(-1 if flip else 1)
        b=panel[ek][asset]; e=b['open']
        if side<0:
            sp=e*(1+stop); ex=sp if (stop and b['high']>=sp) else b['close']; r=(e-ex)/e
        else:
            sp=e*(1-stop); ex=sp if (stop and b['low']<=sp) else b['close']; r=(ex-e)/e
        out.append(r)
    return np.array(out)
r=single(p1,LO,HI,'eur',True,0.0)
print(f"EURUSD 1H FADE: {len(r)} round trips over 8 months")
print(f"gross mean/trade {r.mean()*100:+.5f}%   t=+2.34\n")
print("EURUSD round-trip cost as % of NOTIONAL (spread + commission):")
print(f"{'scenario':>34} {'cost':>9} {'net mean/trade':>16} {'best k':>8} {'8-mo ROI':>16}")
SC=[("institutional ECN 0.1 pip",0.0000100),
    ("tight retail ECN 0.2 pip",0.0000200),
    ("typical retail ECN 0.3 pip",0.0000300),
    ("retail standard 0.5 pip",0.0000500),
    ("retail wide 1.0 pip",0.0001000),
    ("zero cost (unrealistic)",0.0)]
for nm,c in SC:
    net=r-c
    b=None
    for k in np.arange(0.5,300,0.5):
        g=1+net*k
        if (g<=0).any(): break
        v=(np.cumprod(g)[-1]-1)*100
        if b is None or v>b[0]: b=(v,k)
    if b is None: print(f"{nm:>34} {c*100:8.4f}% {net.mean()*100:+15.5f}% {'WIPED':>8} {'-':>16}"); continue
    print(f"{nm:>34} {c*100:8.4f}% {net.mean()*100:+15.5f}% {b[1]:8.1f} {b[0]:15,.2f}%")
print()
be=r.mean()
print(f"BREAK-EVEN cost: {be*100:.5f}% of notional = {be*10000:.3f} pips on EURUSD")
print(f"Tightest real EURUSD spread is ~0.1-0.2 pip + commission ~0.2 pip round trip.")
print(f"-> the edge is {be*10000:.3f} pips; realistic all-in cost is ~0.3-0.5 pip.")
