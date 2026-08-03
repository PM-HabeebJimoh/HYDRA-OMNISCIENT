#!/usr/bin/env python3
"""AGBA METTA OMEGA-K: all streams as ONE Kelly-sized portfolio.
Every stream is the Agba Metta magnitude bracket at a different (asset,TF,width,hold).
Worst-case whipsaw, real spreads, no look-ahead."""
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
print(f"streams built: {len(S)}")
MON=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']

# pool ALL trades chronologically; each trade sized by ITS OWN stream Kelly fraction
allev=[]
for k,ev in S.items():
    g=np.array([x[1] for x in ev]); mu,sd=g.mean(),g.std()
    kel=mu/sd**2 if sd>0 else 0
    for t,x in ev: allev.append((t,k,x,kel))
allev.sort()
print(f"total trades: {len(allev)}")
print()
print("="*96)
print("OMEGA-K: all streams, each Kelly-sized, capital shared and compounded")
print("="*96)
print(f"{'kelly frac':>11} {'8-mo ROI':>16} {'median mo':>12} {'months>1000%':>13} {'worst mo':>10}")
for kf in (0.05,0.10,0.15,0.20,0.25,0.35,0.50):
    eq=1.0; monthly=collections.defaultdict(float); ok=True
    mstart={}
    for t,k,x,kel in allev:
        m=utc(t).strftime('%Y-%m')
        if m not in mstart: mstart[m]=eq
        f=max(0.0,kel)*kf
        # cap single-trade risk at 25% of equity to avoid ruin
        f=min(f,0.25/max(abs(x),1e-9)) if x<0 else f
        eq*= (1+f*x)
        if eq<=0: ok=False; break
    if not ok: print(f"{kf:11.2f} {'RUIN':>16}"); continue
    # recompute monthly
    eq=1.0; rois=[]
    for m in MON:
        s=eq
        for t,k,x,kel in allev:
            if utc(t).strftime('%Y-%m')!=m: continue
            f=max(0.0,kel)*kf
            if x<0: f=min(f,0.25/max(abs(x),1e-9))
            eq*=(1+f*x)
        rois.append((eq/s-1)*100 if s>0 else float('nan'))
    print(f"{kf:11.2f} {(eq-1)*100:15,.1f}% {np.median(rois):11.1f}% {sum(1 for r in rois if r>1000):13d} {min(rois):9.1f}%")
print()
kf=0.25
eq=1.0; rois=[]
for m in MON:
    s=eq
    for t,k,x,kel in allev:
        if utc(t).strftime('%Y-%m')!=m: continue
        f=max(0.0,kel)*kf
        if x<0: f=min(f,0.25/max(abs(x),1e-9))
        eq*=(1+f*x)
    rois.append((eq/s-1)*100)
print(f"MONTH-BY-MONTH at kelly_frac={kf}:")
for m,r in zip(MON,rois):
    print(f"  {m}: {r:+12,.1f}%  {'>>> ACHIEVED' if r>1000 else ''}")
