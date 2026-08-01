#!/usr/bin/env python3
"""ANGLES 7-12 — dimensions I have never tested even once."""
from research.a16_core import *

print("="*100); print("ANGLE 7 (TEMPORAL SLICE) — is the edge a TIME-OF-DAY effect?"); print("="*100)
print("  I aggregated all hours together for 12 sessions. Never split by session.")
for a in A:
    ks,o,h,l,c=arr(p1,a); r=(c-o)/o
    hh=np.array([utc(t).hour for t in ks])
    print(f"  {a}:")
    best=[]
    for H in range(24):
        m=hh==H
        if m.sum()<40: continue
        seg=r[m]
        best.append((abs(T(seg)),H,seg.mean()*1e4,T(seg),m.sum()))
    best.sort(reverse=True)
    for _,H,mu,t,n in best[:3]:
        tag="LONDON OPEN" if H==7 else ("NY OPEN" if H==13 else ("ASIA" if H<6 else ""))
        print(f"     {H:02d}:00 UTC  n={n:4d}  mean={mu:+7.3f}bp  t={t:+6.2f}   {tag}")

print()
print("="*100); print("ANGLE 8 (DAY-OF-WEEK)"); print("="*100)
for a in A:
    ks,o,h,l,c=arr(p1,a); r=(c-o)/o
    dw=np.array([utc(t).weekday() for t in ks])
    out=[]
    for d in range(5):
        m=dw==d; out.append((['Mon','Tue','Wed','Thu','Fri'][d],r[m].mean()*1e4,T(r[m]),m.sum()))
    s=" ".join(f"{n}:{mu:+.2f}bp(t{t:+.1f})" for n,mu,t,_ in out)
    print(f"  {a}: {s}")

print()
print("="*100); print("ANGLE 9 (OVERNIGHT vs INTRADAY) — decompose the return"); print("="*100)
print("  Every test used open->close. NEVER tested close->open (the gap).")
for a in A:
    ks,o,h,l,c=arr(p4,a)
    body=(c-o)/o
    gap=np.zeros(len(o)); gap[1:]=(o[1:]-c[:-1])/c[:-1]
    rep(f"  {a} BODY  open->close",body,"(what I always traded)")
    rep(f"  {a} GAP   close->open",gap[1:],"(never traded)")

print()
print("="*100); print("ANGLE 10 (VOLATILITY REGIME CONDITIONING)"); print("="*100)
print("  Split every test by whether vol is EXPANDING or CONTRACTING.")
for a in A:
    ks,o,h,l,c=arr(p4,a); r=(c-o)/o; av=atr(h,l,c,20)
    rat=np.full(len(c),np.nan)
    for i in range(40,len(c)): rat[i]=av[i]/np.nanmean(av[i-20:i])
    ok=~np.isnan(rat[:-1])
    exp_=(rat[:-1]>1.05)&ok; con=(rat[:-1]<0.95)&ok
    mom=np.sign(r[:-1])*r[1:]
    print(f"  {a}: vol EXPANDING mom t={T(mom[exp_]):+6.2f} (n={exp_.sum():4d})   "
          f"vol CONTRACTING mom t={T(mom[con]):+6.2f} (n={con.sum():4d})")

print()
print("="*100); print("ANGLE 11 (LEAD-LAG) — does one asset PREDICT another?"); print("="*100)
print("  Never tested. Only ever used the 3 as a simultaneous basket.")
ks=np.array(sorted(p1))
R={a:np.array([(p1[k][a]['close']-p1[k][a]['open'])/p1[k][a]['open'] for k in ks]) for a in A}
for src in A:
    for dst in A:
        if src==dst: continue
        pnl=np.sign(R[src][:-1])*R[dst][1:]-COST[dst]
        t=T(pnl)
        flag="  <-- SIGNIFICANT" if abs(t)>2.5 else ""
        print(f"  {src:>5} at t  ->  {dst:>5} at t+1 :  mean={pnl.mean()*1e4:+7.3f}bp  t={t:+6.2f}{flag}")

print()
print("="*100); print("ANGLE 12 (SECOND DERIVATIVE) — trade ACCELERATION not velocity"); print("="*100)
for a in A:
    ks,o,h,l,c=arr(p4,a); r=(c-o)/o
    acc=np.zeros(len(r)); acc[1:]=r[1:]-r[:-1]
    rep(f"  {a} sign(accel) -> next",np.sign(acc[:-1])*r[1:]-COST[a])
