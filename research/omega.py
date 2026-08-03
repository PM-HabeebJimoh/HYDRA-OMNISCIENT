#!/usr/bin/env python3
"""AGBA METTA OMEGA — target: >1000% MONTHLY ROI. DD unconstrained.

Keeps the Agba Metta core (3-asset alignment) but fixes what was broken:
  OLD: alignment -> bet DIRECTION (proven ~50%, R2 0.02%)
  NEW: alignment -> bet MAGNITUDE  (measured R2 8%, alignment => next-bar range 1.10x)

Execution: bracket (buy-stop above / sell-stop below) = direction-neutral.
Honest handling: BOTH triggers in one bar = booked as full double loss (worst case).
Real spreads. No look-ahead: alignment read on CLOSED bar i, bracket placed bar i+1.
"""
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

def signals(P,w,hold,gate):
    """gate: 'none' | 'align' (Agba Metta alignment on the CLOSED prior bar)"""
    ks=np.array(sorted(P))
    AL={}
    for i,k in enumerate(ks):
        b=P[k]
        up=all(b[a]['close']>b[a]['open'] for a in A)
        dn=all(b[a]['close']<b[a]['open'] for a in A)
        AL[k]= up or dn
    out=collections.defaultdict(list)
    for a in A:
        _,o,h,l,c=arr(P,a); av=atr(h,l,c,20); n=len(c)
        for i in range(21,n-hold):
            if np.isnan(av[i]): continue
            if gate=='align' and not AL[ks[i-1]]: continue   # signal from CLOSED bar i-1
            A_=av[i]/o[i]; up=o[i]*(1+w*A_); dn=o[i]*(1-w*A_); s=0; e=None
            for j in range(i,min(i+hold,n)):
                hu=h[j]>=up; hd=l[j]<=dn
                if hu and hd:
                    out[a].append((ks[i],-2*w*A_-2*COST[a])); s=-99; break
                if hu: s=1;e=up;break
                if hd: s=-1;e=dn;break
            if s in (0,-99): continue
            ex=c[min(i+hold-1,n-1)]
            out[a].append((ks[i],((ex-e)/e if s>0 else (e-ex)/e)-2*COST[a]))
    return out

MON=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
def monthly(ev):
    m=collections.defaultdict(list)
    for t,g in ev: m[utc(t).strftime('%Y-%m')].append(g)
    return m

def maxroi(g):
    """hindsight-optimal leverage for THIS month; also report the k."""
    g=np.array(g)
    if len(g)<5: return None
    best=(-1e9,0)
    for k in np.arange(0.5,400,0.5):
        x=1+g*k
        if (x<=0).any(): break
        v=(np.cumprod(x)[-1]-1)*100
        if v>best[0]: best=(v,k)
    return best

print("="*104)
print("AGBA METTA OMEGA — MONTHLY ROI, hindsight-optimal leverage per month")
print("="*104)
print(f"{'config':<34} "+" ".join(f"{m[-5:]:>10}" for m in MON))
rows={}
for tf,P in (('4H',p4),('1H',p1)):
    for gate in ('none','align'):
        for w in (0.5,0.75,1.0):
            for hold in (3,6):
                S=signals(P,w,hold,gate)
                lab=f"{tf} w{w} h{hold} gate={gate}"
                # pooled across the 3 assets, chronological
                allev=sorted([e for a in A for e in S[a]])
                M=monthly(allev)
                out=[]
                for m in MON:
                    r=maxroi(M.get(m,[]))
                    out.append(r[0] if r else float('nan'))
                rows[lab]=out
                if max([x for x in out if x==x],default=0)>300:
                    print(f"{lab:<34} "+" ".join(f"{x:10,.0f}" if x==x else f"{'-':>10}" for x in out))
print()
print("Cells above 1000% (hindsight-optimal k):")
hits=0
for lab,out in rows.items():
    for m,x in zip(MON,out):
        if x==x and x>1000:
            print(f"   {lab:<34} {m}: {x:12,.1f}%"); hits+=1
print(f"   total: {hits}")
