#!/usr/bin/env python3
"""THE REFRAME.

Established: direction R2 ~0.02%, magnitude R2 ~8%. 345x.
Every model in this project bet on the 0.02%. That was the error - not the
parameters, the CHOICE OF WHAT TO BET ON.

If you can predict |move| but not sign, the correct payoff is one that is
LONG VOLATILITY and DIRECTION-NEUTRAL. In options that is a straddle. With
spot only, the synthetic equivalent is a BRACKET: place a buy-stop above and a
sell-stop below. Whichever fires, you are in the direction of the break; the
other is cancelled. You do not need to know WHICH way - only THAT it moves.

P&L per bracket = |move beyond the trigger| - 2*trigger_distance - cost
  wins when realised range > breakout width
  loses a bounded, known amount when it doesn't

This flips the failure mode of Agba Metta: instead of needing 50%+ direction
accuracy (impossible), we need realised range > threshold (predictable, R2=8%).

Test it honestly, on the same real bars, with the same cost model.
"""
import sys, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}

def arr(panel,a):
    ks=sorted(panel)
    return (np.array(ks),
            np.array([panel[k][a]['open']  for k in ks]),
            np.array([panel[k][a]['high']  for k in ks]),
            np.array([panel[k][a]['low']   for k in ks]),
            np.array([panel[k][a]['close'] for k in ks]))

def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a

def bracket(panel,a,w,hold,lo=None,hi=None,vol_filter=None):
    """Bracket entered at bar i open, triggers at open*(1+/-w*atr).
    Direction-agnostic. Exit at close of bar i+hold-1 or opposite stop."""
    ks,o,h,l,c=arr(panel,a); av=atr(h,l,c,20); n=len(c); out=[]
    for i in range(21,n-hold):
        if lo is not None and not (lo<=ks[i]<hi): continue
        if np.isnan(av[i]): continue
        A_=av[i]/o[i]
        if vol_filter is not None and not vol_filter(i,av,o): continue
        up=o[i]*(1+w*A_); dn=o[i]*(1-w*A_)
        side=0; ent=None; j0=None
        for j in range(i,min(i+hold,n)):
            hit_up=h[j]>=up; hit_dn=l[j]<=dn
            if hit_up and hit_dn:      # ambiguous bar - assume worse (whipsaw)
                side=0; break
            if hit_up: side=+1; ent=up; j0=j; break
            if hit_dn: side=-1; ent=dn; j0=j; break
        if side==0: continue
        ex=c[min(i+hold-1,n-1)]
        g=(ex-ent)/ent if side>0 else (ent-ex)/ent
        out.append((ks[i],g-2*COST[a],A_))
    return out

print("="*92)
print("REFRAME — DIRECTION-AGNOSTIC BRACKET (synthetic straddle) on real bars")
print("="*92)
print("Bet on MAGNITUDE (R2 8%) not DIRECTION (R2 0.02%). Cost = 2 legs.")
print()
print(f"{'TF':>4} {'asset':>6} {'width':>6} {'hold':>5} {'n':>5} {'WR':>7} {'mean%':>9} {'t':>7}")
best=[]
for tf,pan in (('1H',p1),('4H',p4)):
    for a in A:
        for w in (0.25,0.5,0.75,1.0):
            for hold in (3,6,12):
                ev=bracket(pan,a,w,hold)
                if len(ev)<50: continue
                g=np.array([e[1] for e in ev])
                t=g.mean()/(g.std()/np.sqrt(len(g)))
                best.append((t,tf,a,w,hold,g))
                if t>2.0:
                    print(f"{tf:>4} {a:>6} {w:6.2f} {hold:5d} {len(g):5d} {(g>0).mean()*100:6.2f}% {g.mean()*100:+8.4f} {t:+7.2f}")
print()
best.sort(reverse=True)
print("TOP 6 BY t-STAT (all configs, including negative):")
for t,tf,a,w,hold,g in best[:6]:
    print(f"  {tf} {a:>5} width={w} hold={hold}: n={len(g)} mean={g.mean()*100:+.4f}% t={t:+.2f}")
print()
print("="*92)
print("COMPARE HEAD-TO-HEAD ON IDENTICAL BARS")
print("="*92)
print("Same asset, same period. Directional bet vs magnitude bet.")
for a in A:
    ks,o,h,l,c=arr(p1,a)
    r=(c-o)/o
    # directional: previous-bar momentum
    d=np.sign(r[:-1])*r[1:]
    d=d[~np.isnan(d)]
    ev=bracket(p1,a,0.5,6)
    g=np.array([e[1] for e in ev])
    print(f"  {a:>5}: DIRECTIONAL n={len(d):5d} t={d.mean()/(d.std()/np.sqrt(len(d))):+6.2f}   "
          f"|  BRACKET n={len(g):5d} t={g.mean()/(g.std()/np.sqrt(len(g))):+6.2f}")
