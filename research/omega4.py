#!/usr/bin/env python3
"""My shuffle control was INVALID: prod(1+k*r) is order-invariant, so shuffling
cannot change the answer. p=0.940 was meaningless. Use the valid controls."""
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
def ev_for(w,hold,flip=None):
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
            g=((ex-e)/e if s>0 else (e-ex)/e)-2*COST[a]
            out.append((ks[i],g))
    return sorted(out)
ev=ev_for(0.75,3)
M=collections.defaultdict(list)
for t,g in ev: M[utc(t).strftime('%Y-%m')].append(g)
jan=np.array(M['2026-01'])
print("="*94); print("VALID CONTROL: sign-flip the BARS (kills edge, keeps magnitudes)"); print("="*94)
def maxroi(g):
    g=np.array(g); best=-1e9
    for k in np.arange(0.5,400,0.5):
        x=1+g*k
        if (x<=0).any(): break
        best=max(best,(np.cumprod(x)[-1]-1)*100)
    return best
act=maxroi(jan)
rng=np.random.default_rng(3)
null=[maxroi(jan*rng.choice([-1.0,1.0],len(jan))) for _ in range(300)]
null=np.array(null)
print(f"  actual Jan hindsight ROI = {act:,.0f}%")
print(f"  sign-flipped null: median {np.median(null):,.0f}%  95th {np.percentile(null,95):,.0f}%  max {null.max():,.0f}%")
print(f"  p = {(null>=act).mean():.3f}  -> {'REAL' if (null>=act).mean()<0.05 else 'NOISE'}")
print(f"\n  Jan raw edge: mean={jan.mean()*100:+.4f}% t={jan.mean()/(jan.std()/np.sqrt(len(jan))):+.2f}")
print()
print("="*94); print("FINAL HONEST ANSWER — single k, all months, real spreads"); print("="*94)
best=(-1e9,0,None)
for k in np.arange(0.5,200,0.5):
    rois=[]; ok=True
    for m in sorted(M):
        x=1+np.array(M[m])*k
        if (x<=0).any(): ok=False; break
        rois.append((np.cumprod(x)[-1]-1)*100)
    if not ok: break
    if np.median(rois)>best[0]: best=(np.median(rois),k,rois)
med,k,rois=best
print(f"  k={k:.1f}  median monthly {med:+.1f}%  months>1000%: {sum(1 for r in rois if r>1000)}/8")
print(f"  compounded 8-month: ",end="")
eq=1.0
for r in rois: eq*= (1+r/100)
print(f"{(eq-1)*100:,.1f}%")
print(f"  worst month {min(rois):+.1f}%  -> that is the drawdown you accept")
