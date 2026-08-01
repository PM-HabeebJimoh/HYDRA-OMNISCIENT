#!/usr/bin/env python3
"""Spec needs ann Sharpe ~13. Where am I, and can stacking INDEPENDENT streams close it?
Sharpe scales sqrt(N_eff). Build every non-redundant bracket stream from real bars."""
import sys, itertools, numpy as np, math
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
p1=load_1h(); p4=resample_4h(p1)
def arr(P,a):
    ks=sorted(P); return (np.array(ks),*(np.array([P[k][a][f] for k in ks]) for f in ('open','high','low','close')))
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a
def brk(P,a,w,hold,off=0):
    ks,o,h,l,c=arr(P,a); av=atr(h,l,c,20); n=len(c); ts=[];g=[]
    for i in range(21+off,n-hold,max(hold,1)):
        if np.isnan(av[i]): continue
        A_=av[i]/o[i]; up=o[i]*(1+w*A_); dn=o[i]*(1-w*A_); s=0; e=None
        for j in range(i,min(i+hold,n)):
            hu=h[j]>=up; hd=l[j]<=dn
            if hu and hd: g.append(-2*w*A_-2*COST[a]); ts.append(ks[i]); s=-99; break
            if hu: s=1;e=up;break
            if hd: s=-1;e=dn;break
        if s in (0,-99): continue
        ex=c[min(i+hold-1,n-1)]
        g.append(((ex-e)/e if s>0 else (e-ex)/e)-2*COST[a]); ts.append(ks[i])
    return np.array(ts),np.array(g)

print("="*92); print("STEP 1 — where am I vs the spec?"); print("="*92)
ts,g=brk(p4,'gold',1.0,3)
tr_yr=len(g)/8*12
sr_tr=g.mean()/g.std(); sr_ann=sr_tr*math.sqrt(tr_yr)
print(f"  gold 4H bracket: n={len(g)} per-trade SR={sr_tr:.4f} -> ANNUAL SHARPE = {sr_ann:.2f}")
print(f"  SPEC REQUIRES  : ~13.0")
print(f"  GAP            : {13/sr_ann:.1f}x  -> need {(13/sr_ann)**2:.0f} INDEPENDENT streams")

print("\n"+"="*92); print("STEP 2 — build every candidate stream"); print("="*92)
S={}
for a in A:
    for w in (0.75,1.0,1.5):
        for hold in (3,6):
            for P,tf in ((p4,'4H'),(p1,'1H')):
                t_,x=brk(P,a,w,hold)
                if len(x)<80: continue
                sr=x.mean()/x.std()*math.sqrt(len(x)/8*12)
                if sr>0.5: S[f"{a}-{tf}-w{w}-h{hold}"]=(t_,x,sr)
print(f"  streams with ann SR > 0.5 : {len(S)}")
for k,(t_,x,sr) in sorted(S.items(),key=lambda z:-z[1][2])[:10]:
    print(f"    {k:<22} n={len(x):5d} annSR={sr:5.2f}")

print("\n"+"="*92); print("STEP 3 — how independent are they REALLY?"); print("="*92)
keys=list(S)
if len(keys)>=2:
    # align on common timestamps
    common=set(S[keys[0]][0])
    for k in keys[1:]: common&=set(S[k][0])
    common=np.array(sorted(common))
    if len(common)>50:
        M=np.column_stack([np.array([dict(zip(S[k][0],S[k][1]))[t] for t in common]) for k in keys])
        C=np.corrcoef(M.T); ev=np.linalg.eigvalsh(C)[::-1]
        neff=(ev.sum()**2)/(ev**2).sum()
        print(f"  aligned bars={len(common)}  streams={len(keys)}")
        print(f"  mean pairwise |corr| = {np.abs(C[np.triu_indices(len(keys),1)]).mean():.3f}")
        print(f"  PARTICIPATION RATIO N_eff = {neff:.2f}  (not {len(keys)})")
        w=np.ones(len(keys))/len(keys); port=(M*w).sum(1)
        psr=port.mean()/port.std()*math.sqrt(len(port)/8*12)
        print(f"  equal-weight portfolio ANNUAL SHARPE = {psr:.2f}")
        print(f"  best single stream                   = {max(v[2] for v in S.values()):.2f}")
        print(f"\n  SPEC 13.0 vs ACHIEVED {psr:.2f}  -> still {13/max(psr,.01):.1f}x short")
        need=(13/max(psr,.01))**2
        print(f"  would need {need:.0f}x more INDEPENDENT streams (N_eff, not count)")
