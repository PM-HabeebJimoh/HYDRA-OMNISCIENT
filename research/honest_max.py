#!/usr/bin/env python3
"""What does the margin denominator ACTUALLY buy, at survivable risk?
Gold-only (the one stream with a verified edge), Kelly-bounded."""
import sys, numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
p4=resample_4h(load_1h())
def arr(a):
    ks=sorted(p4)
    return (np.array([p4[k][a]['open'] for k in ks]),np.array([p4[k][a]['high'] for k in ks]),
            np.array([p4[k][a]['low'] for k in ks]),np.array([p4[k][a]['close'] for k in ks]))
o,h,l,c=arr('gold')
n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
av=np.full(n,np.nan)
for i in range(19,n): av[i]=tr[i-19:i+1].mean()
g=[]
for i in range(21,n-3):
    if np.isnan(av[i]): continue
    A_=av[i]/o[i]; up=o[i]*(1+A_); dn=o[i]*(1-A_); side=0; ent=None
    for j in range(i,min(i+3,n)):
        hu=h[j]>=up; hd=l[j]<=dn
        if hu and hd: g.append(-2*A_-0.00014); side=-99; break
        if hu: side=1; ent=up; break
        if hd: side=-1; ent=dn; break
    if side in (0,-99): continue
    ex=c[min(i+2,n-1)]
    g.append(((ex-ent)/ent if side>0 else (ent-ex)/ent)-0.00014)
g=np.array(g)
mu,sd=g.mean(),g.std()
kelly=mu/sd**2
print("="*88); print("GOLD 4H BRACKET — HONEST SIZING"); print("="*88)
print(f"  n={len(g)}  mean={mu*100:+.4f}%  sd={sd*100:.4f}%  t={mu/(sd/np.sqrt(len(g))):+.2f}")
print(f"  full-Kelly leverage = mu/sd^2 = {kelly:.1f}x")
print(f"  worst single trade  = {g.min()*100:.2f}%\n")
print(f"  {'sizing':>22} {'lev':>6} {'8-mo ROI':>13} {'maxDD':>9} {'verdict':>12}")
for nm,f in (("quarter-Kelly",0.25),("half-Kelly",0.5),("full-Kelly",1.0),("2x Kelly",2.0)):
    lev=kelly*f; eq=np.cumprod(1+g*lev)
    if (1+g*lev).min()<=0: print(f"  {nm:>22} {lev:6.1f} {'RUIN':>13}"); continue
    pk=np.maximum.accumulate(eq); dd=((eq-pk)/pk).min()*100
    v="tradeable" if dd>-35 else ("aggressive" if dd>-60 else "RUIN-RISK")
    print(f"  {nm:>22} {lev:6.1f} {(eq[-1]-1)*100:12,.2f}% {dd:8.2f}% {v:>12}")
print()
print("  On CME gold futures (5% margin, so 20x notional available):")
print(f"  half-Kelly needs {kelly*0.5:.0f}x -> FITS inside futures margin.")
print(f"  Retail spot at 1x notional CANNOT express this. The denominator is the")
print(f"  binding constraint on ROI, not the edge.")
