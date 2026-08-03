#!/usr/bin/env python3
"""WHY hindsight gives 67,982% and honest walk-forward gives 0/30.
Run the IDENTICAL hindsight-optimal procedure on RANDOM data."""
import sys, collections, datetime
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
p4=resample_4h(load_1h())
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
def arr(P,a):
    ks=sorted(P); return (np.array(ks),*(np.array([P[k][a][f] for k in ks]) for f in ('open','high','low','close')))
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a
def ev_for(w,hold):
    out=[]
    for a in A:
        ks,o,h,l,c=arr(p4,a); av=atr(h,l,c,20); n=len(c)
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
    return sorted(out)
def maxroi(g):
    g=np.array(g); best=-1e9
    for k in np.arange(0.5,400,0.5):
        x=1+g*k
        if (x<=0).any(): break
        best=max(best,(np.cumprod(x)[-1]-1)*100)
    return best
ev=ev_for(0.75,3)
M=collections.defaultdict(list)
for t,g in ev: M[utc(t).strftime('%Y-%m')].append(g)
jan=np.array(M['2026-01'])
print("="*94)
print("THE 67,982% JANUARY CELL — dissected")
print("="*94)
print(f"  n={len(jan)} trades, mean={jan.mean()*100:+.4f}%, t={jan.mean()/(jan.std()/np.sqrt(len(jan))):+.2f}")
print(f"  hindsight-optimal ROI = {maxroi(jan):,.0f}%")
print()
print("  CONTROL: same hindsight procedure on SHUFFLED versions of the SAME trades.")
print("  (shuffling destroys any time-structure but keeps the exact return distribution)")
rng=np.random.default_rng(0)
sh=[maxroi(rng.permutation(jan)) for _ in range(200)]
print(f"    shuffled median {np.median(sh):,.0f}%   95th {np.percentile(sh,95):,.0f}%   max {max(sh):,.0f}%")
print(f"    actual {maxroi(jan):,.0f}%  ->  p = {(np.array(sh)>=maxroi(jan)).mean():.3f}")
print()
print("  CONTROL: same procedure on RANDOM returns with the same mean/sd.")
rd=[maxroi(rng.normal(jan.mean(),jan.std(),len(jan))) for _ in range(200)]
print(f"    random-normal median {np.median(rd):,.0f}%   95th {np.percentile(rd,95):,.0f}%")
print()
print("  Optimising k with hindsight on ANY series with positive mean produces")
print("  astronomic numbers. It measures the optimiser, not the market.")
print()
print("="*94); print("WHAT IS THE REAL MONTHLY CEILING?"); print("="*94)
print("  Honest test: single k fixed across ALL 8 months (no per-month tuning).")
best=(-1e9,0)
for k in np.arange(0.5,200,0.5):
    rois=[]
    ok=True
    for m in sorted(M):
        g=np.array(M[m]); x=1+g*k
        if (x<=0).any(): ok=False; break
        rois.append((np.cumprod(x)[-1]-1)*100)
    if not ok: break
    if np.median(rois)>best[0]: best=(np.median(rois),k,rois)
med,k,rois=best
print(f"  best single k = {k:.1f}  median monthly ROI = {med:+.2f}%")
print(f"  {'month':>8} {'ROI':>12}")
for m,r in zip(sorted(M),rois): print(f"  {m:>8} {r:+11.2f}%")
print(f"\n  months >1000%: {sum(1 for r in rois if r>1000)}/8")
