#!/usr/bin/env python3
"""HONEST OMEGA-K: Kelly fractions estimated from PRIOR data only, expanding window.
No look-ahead anywhere. This is the tradeable version."""
import sys, datetime, collections, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
p1=load_1h(); p4=resample_4h(p1)
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
def arr(P,a):
    ks=sorted(P); return (np.array(ks),*(np.array([P[k][a][f] for k in ks]) for f in ('open','high','low','close')))
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a
def stream(P,a,w,hold):
    ks,o,h,l,c=arr(P,a); av=atr(h,l,c,20); n=len(c); out=[]
    for i in range(21,n-hold):
        if np.isnan(av[i]): continue
        A_=av[i]/o[i]; up=o[i]*(1+w*A_); dn=o[i]*(1-w*A_); s=0; e=None
        for j in range(i,min(i+hold,n)):
            hu=h[j]>=up; hd=l[j]<=dn
            if hu and hd: out.append((ks[i],-2*w*A_-2*COST[a])); s=-99; break
            if hu: s=1;e=up;break
            if hd: s=-1;e=dn;break
        if s in (0,-99): continue
        ex=c[min(i+hold-1,n-1)]
        out.append((ks[i],((ex-e)/e if s>0 else (e-ex)/e)-2*COST[a]))
    return out
S={}
for a in A:
    for P,tf in ((p4,'4H'),(p1,'1H')):
        for w in (0.5,0.75,1.0):
            for hold in (3,6):
                ev=stream(P,a,w,hold)
                if len(ev)>=100: S[f"{a}|{tf}|w{w}|h{hold}"]=ev
allev=sorted([(t,k,x) for k,ev in S.items() for t,x in ev])
MON=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
print("="*98)
print("HONEST OMEGA-K — Kelly from PRIOR trades only (expanding window), no look-ahead")
print("="*98)
print(f"streams={len(S)}  trades={len(allev)}")
print(f"\n{'kf':>6} {'8-mo ROI':>18} {'median mo':>11} {'>1000% months':>14} {'worst mo':>10}")
BEST=None
for kf in (0.05,0.10,0.15,0.20,0.25,0.35,0.50,0.75,1.0):
    hist=collections.defaultdict(list); eq=1.0; rois=[]; ok=True
    mi=0
    for m in MON:
        s=eq
        for t,k,x in allev:
            if utc(t).strftime('%Y-%m')!=m: continue
            h=hist[k]
            if len(h)>=30:
                g=np.array(h); mu,sd=g.mean(),g.std()
                kel=max(0.0,mu/sd**2) if sd>0 else 0.0
            else: kel=0.0
            f=kel*kf
            if x<0: f=min(f,0.25/max(abs(x),1e-9))
            eq*=(1+f*x)
            hist[k].append(x)
            if eq<=0: ok=False; break
        if not ok: break
        rois.append((eq/s-1)*100)
    if not ok: print(f"{kf:6.2f} {'RUIN':>18}"); continue
    n1000=sum(1 for r in rois if r>1000)
    print(f"{kf:6.2f} {(eq-1)*100:17,.1f}% {np.median(rois):10.1f}% {n1000:14d} {min(rois):9.1f}%")
    if BEST is None or n1000>BEST[0]: BEST=(n1000,kf,rois,eq)
n1000,kf,rois,eq=BEST
print(f"\nBEST: kelly_frac={kf}  months>1000%={n1000}/8")
for m,r in zip(MON,rois):
    print(f"  {m}: {r:+13,.1f}%  {'>>> ACHIEVED' if r>1000 else ''}")
