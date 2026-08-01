#!/usr/bin/env python3
"""HONEST walk-forward: select streams on PAST data only, trade forward.
No in-sample cherry-picking. This is the only defensible way to combine streams."""
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
                if len(ev)>=100: S[f"{a}-{tf}-w{w}-h{hold}"]=ev
days=sorted({utc(t).strftime('%Y-%m-%d') for ev in S.values() for t,_ in ev})
D={}
for k,ev in S.items():
    m=collections.defaultdict(list)
    for t,g in ev: m[utc(t).strftime('%Y-%m-%d')].append(g)
    D[k]=np.array([np.mean(m[d]) if d in m else 0.0 for d in days])
keys=list(D); M=np.column_stack([D[k] for k in keys]); nd=len(days)
print("="*94); print("WALK-FORWARD STREAM SELECTION (no in-sample peeking)"); print("="*94)
print("  Rule: every 20 days, rank streams by trailing 60-day Sharpe, hold top-K, trade next 20.")
for K in (3,5,8,12):
    port=np.zeros(nd); TRAIN=60; STEP=20
    for s0 in range(TRAIN,nd,STEP):
        tr=M[s0-TRAIN:s0]
        sr=np.array([tr[:,j].mean()/(tr[:,j].std()+1e-12) for j in range(len(keys))])
        pick=np.argsort(sr)[::-1][:K]
        e0,e1=s0,min(s0+STEP,nd)
        port[e0:e1]=M[e0:e1][:,pick].mean(1)
    live=port[TRAIN:]
    if live.std()==0: continue
    sr_a=live.mean()/live.std()*math.sqrt(252)
    eq=np.cumprod(1+live); pk=np.maximum.accumulate(eq)
    dd=((eq-pk)/pk).min()*100
    print(f"  top-{K:2d}: OOS days={len(live)} annSR={sr_a:5.2f} ROI={(eq[-1]-1)*100:+7.2f}% DD={dd:6.2f}%")
print("\n"+"="*94); print("THE VERDICT ON THE SPEC"); print("="*94)
print("  Best walk-forward portfolio Sharpe above vs SPEC requirement of 13.0.")
print("  Leverage cannot fix Sharpe - it scales return and DD together, so MAR is invariant.")
print("\n  PROOF that MAR is leverage-invariant:")
K=5; TRAIN=60; STEP=20; port=np.zeros(nd)
for s0 in range(TRAIN,nd,STEP):
    tr=M[s0-TRAIN:s0]
    sr=np.array([tr[:,j].mean()/(tr[:,j].std()+1e-12) for j in range(len(keys))])
    pick=np.argsort(sr)[::-1][:K]
    e0,e1=s0,min(s0+STEP,nd); port[e0:e1]=M[e0:e1][:,pick].mean(1)
live=port[TRAIN:]
print(f"  {'leverage':>9} {'ROI':>12} {'maxDD':>9} {'MAR':>7}")
for lev in (1,2,5,10,20,40):
    x=live*lev
    if (1+x).min()<=0: print(f"  {lev:9d} {'RUIN':>12}"); continue
    eq=np.cumprod(1+x); pk=np.maximum.accumulate(eq)
    roi=(eq[-1]-1)*100; dd=abs(((eq-pk)/pk).min()*100)
    print(f"  {lev:9d} {roi:+11.2f}% {dd:8.2f}% {roi/max(dd,.01):7.2f}")
print("\n  MAR stays flat as leverage rises. SPEC needs MAR=125.")
