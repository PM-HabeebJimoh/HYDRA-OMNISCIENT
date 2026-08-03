#!/usr/bin/env python3
"""Measure TRUE independence by aggregating every stream onto a common DAILY grid."""
import sys, datetime, collections, numpy as np, math
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
def brk(P,a,w,hold):
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
    for w in (0.75,1.0,1.5):
        for hold in (3,6):
            for P,tf in ((p4,'4H'),(p1,'1H')):
                ev=brk(P,a,w,hold)
                if len(ev)<100: continue
                S[f"{a}-{tf}-w{w}-h{hold}"]=ev
print("="*94); print("TRUE INDEPENDENCE — daily-aggregated streams"); print("="*94)
days=sorted({utc(t).strftime('%Y-%m-%d') for ev in S.values() for t,_ in ev})
D={}
for k,ev in S.items():
    m=collections.defaultdict(list)
    for t,g in ev: m[utc(t).strftime('%Y-%m-%d')].append(g)
    D[k]=np.array([np.mean(m[d]) if d in m else 0.0 for d in days])
keys=list(D); M=np.column_stack([D[k] for k in keys])
C=np.corrcoef(M.T); ev_=np.linalg.eigvalsh(C)[::-1]
neff=(ev_.sum()**2)/(ev_**2).sum()
print(f"  streams={len(keys)}  trading days={len(days)}")
print(f"  mean pairwise |corr| = {np.abs(C[np.triu_indices(len(keys),1)]).mean():.3f}")
print(f"  PC1 explains {ev_[0]/ev_.sum()*100:.1f}%")
print(f"  N_eff (participation ratio) = {neff:.2f}  from {len(keys)} nominal streams")
print(f"\n  {'stream':<24} {'ann SR':>8}")
for k in keys:
    x=D[k]; print(f"  {k:<24} {x.mean()/x.std()*math.sqrt(252):8.2f}")
w=np.ones(len(keys))/len(keys); port=(M*w).sum(1)
psr=port.mean()/port.std()*math.sqrt(252)
best=max(D[k].mean()/D[k].std()*math.sqrt(252) for k in keys)
print(f"\n  equal-weight PORTFOLIO ann Sharpe = {psr:.2f}")
print(f"  best SINGLE stream                = {best:.2f}")
print(f"  diversification gain              = {psr/best:.2f}x  (sqrt(N_eff) would be {math.sqrt(neff):.2f}x)")
print(f"\n  SPEC = 13.0.  ACHIEVED = {psr:.2f}.  SHORT BY {13/psr:.1f}x")
print(f"  To reach 13 by diversification alone needs N_eff = {(13/best)**2:.0f}")
print(f"  I have N_eff = {neff:.2f} from 3 correlated USD instruments.")
eq=np.cumprod(1+port*1.0); pk=np.maximum.accumulate(eq)
print(f"\n  portfolio at 1x: ROI={(eq[-1]-1)*100:+.2f}% maxDD={((eq-pk)/pk).min()*100:.2f}%")
for lev in (2,5,10,20):
    e2=np.cumprod(1+port*lev)
    if (1+port*lev).min()<=0: print(f"  lev {lev:2d}x: RUIN"); continue
    p2=np.maximum.accumulate(e2)
    print(f"  lev {lev:2d}x: ROI={(e2[-1]-1)*100:+12,.2f}% maxDD={((e2-p2)/p2).min()*100:7.2f}%")
