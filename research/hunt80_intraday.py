"""Same >=80% hunt on 4H and 1H for the core 3 (only pairs with intraday OHLC).
More bars = tighter confidence intervals = a real 80% would be visible."""
import math, itertools
import numpy as np
from research.data import panels
P=panels()
def wilson(k,nn):
    p=k/nn; z=1.96; den=1+z*z/nn
    c=(p+z*z/(2*nn))/den; h=z*math.sqrt(p*(1-p)/nn+z*z/(4*nn*nn))/den
    return c-h,c+h
NAMES=('XAUUSD','EURUSD','AUDUSD')
for tf in ('H4','H1'):
    d=P[tf]; R=(d['C']-d['O'])/d['O']; S=np.sign(R); n=len(R)
    al=S.sum(1); fire=np.abs(al)==3; st=np.abs(R).mean(1)
    print(f"=== {tf}  {n} bars (2026 + Dec25) ===")
    best=[]
    for th in (0.0,0.001,0.002,0.003,0.005,0.008):
        f=fire&(st>=th)
        for j in range(3):
            nx=S[1:,j]; mask=f[:-1]&(nx!=0); nn=int(mask.sum())
            if nn<20: continue
            for mode in (1,-1):
                sig=np.sign(al[:-1])*mode
                k=int((sig[mask]==nx[mask]).sum())
                best.append((k/nn,nn,k,NAMES[j],mode,th))
    best.sort(reverse=True)
    print(f"  {'acc%':>7} {'n':>5} {'95% CI':>15} {'target':>8} {'dir':>7} {'minstr':>8}")
    for a,nn,k,nm,mode,th in best[:6]:
        lo,hi=wilson(k,nn)
        print(f"  {a*100:7.2f} {nn:5d} [{lo*100:5.1f},{hi*100:5.1f}] {nm:>8} {'follow' if mode>0 else 'fade':>7} {th*100:7.2f}%")
    top=best[0]
    print(f"  best = {top[0]*100:.1f}%  -> {'>=80%' if top[0]>=0.8 else 'BELOW 80%'} "
          f"(need {int(0.8*top[1])} of {top[1]} correct; got {top[2]})\n")
