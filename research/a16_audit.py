#!/usr/bin/env python3
"""AUDIT ANGLE 11 — I flagged 3 lead-lags as SIGNIFICANT. Were they?"""
from research.a16_core import *
ks=np.array(sorted(p1))
R={a:np.array([(p1[k][a]['close']-p1[k][a]['open'])/p1[k][a]['open'] for k in ks]) for a in A}
print("="*96)
print("SELF-AUDIT: the A11 'SIGNIFICANT' flags")
print("="*96)
print("I printed  sign(src_t) * dst_t+1  MINUS COST  and flagged |t|>2.5.")
print("Subtracting a constant cost from a ~zero series makes t significantly")
print("NEGATIVE by construction. That is not a signal - it is the cost.\n")
print(f"{'pair':>14} {'GROSS mean':>12} {'GROSS t':>9} {'cost':>7} {'NET mean':>10} {'NET t':>8}")
for src,dst in (('gold','eur'),('eur','aud'),('aud','eur')):
    g=np.sign(R[src][:-1])*R[dst][1:]
    c=COST[dst]
    print(f"  {src:>5}->{dst:<5} {g.mean()*1e4:+11.3f}bp {T(g):+9.2f} {c*1e4:6.2f}bp "
          f"{(g-c).mean()*1e4:+9.3f}bp {T(g-c):+8.2f}")
print()
print("VERDICT: gross t-stats are all |t| < 1. The 'significance' was the cost")
print("term, not the market. My A11 flag was wrong and I am withdrawing it.")
print()
print("="*96); print("WHAT ACTUALLY SURVIVES ALL 16 ANGLES"); print("="*96)
# the one survivor, re-verified end-to-end
o=np.array([p4[k]['gold']['open'] for k in sorted(p4)])
h=np.array([p4[k]['gold']['high'] for k in sorted(p4)])
l=np.array([p4[k]['gold']['low']  for k in sorted(p4)])
c=np.array([p4[k]['gold']['close']for k in sorted(p4)])
av=atr(h,l,c,20); n=len(c); g=[]
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
print(f"  GOLD 4H VOLATILITY BRACKET (A2 magnitude): n={len(g)} mean={g.mean()*100:+.4f}% t={T(g):+.2f}")
print(f"  This is the ONLY construct that survived all 16 angles + bias audits.")
print()
print(f"  {'sizing':>16} {'lev':>6} {'8-mo ROI':>13} {'maxDD':>9}")
k=g.mean()/g.var()
for nm,f in (("quarter-Kelly",.25),("half-Kelly",.5),("full-Kelly",1.0)):
    lev=k*f; eq=np.cumprod(1+g*lev); pk=np.maximum.accumulate(eq)
    print(f"  {nm:>16} {lev:6.1f} {(eq[-1]-1)*100:12,.2f}% {((eq-pk)/pk).min()*100:8.2f}%")
