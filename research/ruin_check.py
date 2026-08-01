#!/usr/bin/env python3
"""A -100.0% month means the account hit zero. Any 'return' after that is fiction.
Enforce hard ruin: once equity <= 0 (or <1% of start), the test is OVER."""
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
print("="*100)
print("RUIN-ENFORCED OMEGA-K  (account dies at -99%; nothing after that counts)")
print("="*100)
print(f"{'kf':>6} {'survived?':>10} {'8-mo ROI':>16} {'median mo':>11} {'>1000%':>8} {'worst mo':>10} {'maxDD':>9}")
res=[]
for kf in (0.02,0.03,0.05,0.075,0.10,0.15,0.20,0.25):
    hist=collections.defaultdict(list); eq=1.0; peak=1.0; mdd=0.0
    rois=[]; dead=False
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
            eq*=(1+f*x); hist[k].append(x)
            peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
            if eq<=0.01: dead=True; break
        rois.append((eq/s-1)*100 if s>0 else -100.0)
        if dead: break
    n1000=sum(1 for r in rois if r>1000)
    print(f"{kf:6.3f} {'NO-RUINED' if dead else 'yes':>10} {(eq-1)*100:15,.1f}% "
          f"{np.median(rois):10.1f}% {n1000:8d} {min(rois):9.1f}% {mdd*100:8.1f}%")
    if not dead: res.append((n1000,np.median(rois),kf,rois,eq,mdd))
print()
if res:
    res.sort(reverse=True)
    n1000,med,kf,rois,eq,mdd=res[0]
    print(f"BEST SURVIVING CONFIG: kelly_frac={kf}")
    print(f"  8-month ROI {(eq-1)*100:,.1f}%   median monthly {med:.1f}%   maxDD {mdd*100:.1f}%")
    print(f"  months >1000%: {n1000}/8")
    for m,r in zip(MON,rois):
        print(f"    {m}: {r:+12,.1f}%  {'>>> ACHIEVED' if r>1000 else ''}")
