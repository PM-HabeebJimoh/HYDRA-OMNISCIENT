#!/usr/bin/env python3
"""Sigma^-1 mu on 36 streams / 200 days is a textbook overfit (36x36 covariance
from 200 obs). Test it HONESTLY: weights from prior data only."""
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
keys=list(S)
days=sorted({utc(t).strftime('%Y-%m-%d') for ev in S.values() for t,_ in ev})
D={}
for k,ev in S.items():
    m=collections.defaultdict(list)
    for t,g in ev: m[utc(t).strftime('%Y-%m-%d')].append(g)
    D[k]=np.array([np.sum(m[d]) if d in m else 0.0 for d in days])
M=np.column_stack([D[k] for k in keys]); nd=len(days)
print("="*98); print("IN-SAMPLE vs OUT-OF-SAMPLE KELLY WEIGHTS"); print("="*98)
mu=M.mean(0); Sig=np.cov(M.T)+np.eye(len(keys))*1e-10
w_is=np.linalg.pinv(Sig)@mu
p_is=M@w_is
print(f"  IN-SAMPLE  Sigma^-1 mu : ann Sharpe {p_is.mean()/p_is.std()*math.sqrt(252):.2f}  <- fitted on same 200 days")
print()
TRAIN=100; STEP=10
for shrink,lab in ((0.0,'no shrinkage'),(0.5,'50% shrink to diag'),(0.9,'90% shrink to diag'),(1.0,'diagonal only')):
    oos=np.zeros(nd)
    for s0 in range(TRAIN,nd,STEP):
        tr=M[:s0]
        m_=tr.mean(0); C_=np.cov(tr.T)
        Cd=np.diag(np.diag(C_))
        Cs=(1-shrink)*C_+shrink*Cd+np.eye(len(keys))*1e-12
        try: w=np.linalg.pinv(Cs)@m_
        except Exception: continue
        n=np.abs(w).sum()
        if n>0: w=w/n
        e1=min(s0+STEP,nd)
        oos[s0:e1]=M[s0:e1]@w
    live=oos[TRAIN:]
    if live.std()==0: continue
    s=live.mean()/live.std()*math.sqrt(252)
    mx=(math.exp(max(s,0)**2/24)-1)*100
    print(f"  OOS {lab:<22} ann Sharpe {s:6.2f}   implied max monthly ROI {mx:10,.1f}%")
print()
print("="*98); print("SIMPLE ROBUST ALTERNATIVES (no matrix inversion)"); print("="*98)
for lab,w in (("equal weight",np.ones(len(keys))/len(keys)),
              ("inverse-vol",(1/(M.std(0)+1e-12))/np.sum(1/(M.std(0)+1e-12)))):
    pd_=M@w; s=pd_.mean()/pd_.std()*math.sqrt(252)
    print(f"  {lab:<16} ann Sharpe {s:6.2f}   max monthly ROI {(math.exp(max(s,0)**2/24)-1)*100:10,.1f}%")
# OOS inverse-vol with positive-mean screen
oos=np.zeros(nd)
for s0 in range(TRAIN,nd,STEP):
    tr=M[:s0]; m_=tr.mean(0); sd=tr.std(0)+1e-12
    w=np.where(m_>0,1/sd,0.0)
    if w.sum()==0: continue
    w=w/w.sum(); e1=min(s0+STEP,nd); oos[s0:e1]=M[s0:e1]@w
live=oos[TRAIN:]
s=live.mean()/live.std()*math.sqrt(252)
print(f"  {'OOS inv-vol, mu>0':<16} ann Sharpe {s:6.2f}   max monthly ROI {(math.exp(max(s,0)**2/24)-1)*100:10,.1f}%")
print(f"\n  TARGET: ann Sharpe {math.sqrt(24*math.log(11)):.2f} for >1000%/month")
