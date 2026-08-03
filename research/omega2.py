#!/usr/bin/env python3
"""HONEST TEST: leverage fixed IN ADVANCE, never peeking at the month being traded.
Rule: k chosen from PRIOR months only (walk-forward), then applied to the next month."""
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
    ks=np.array(sorted(P)); AL={}
    for k in ks:
        b=P[k]
        AL[k]= all(b[a]['close']>b[a]['open'] for a in A) or all(b[a]['close']<b[a]['open'] for a in A)
    out=[]
    for a in A:
        _,o,h,l,c=arr(P,a); av=atr(h,l,c,20); n=len(c)
        for i in range(21,n-hold):
            if np.isnan(av[i]): continue
            if gate=='align' and not AL[ks[i-1]]: continue
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
MON=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']

print("="*100)
print("HONEST WALK-FORWARD: k from PRIOR months only, applied to next month")
print("="*100)
CFG=[('4H',p4,0.75,3,'none'),('4H',p4,1.0,3,'none'),('4H',p4,1.0,3,'align'),
     ('4H',p4,0.75,6,'none'),('1H',p1,1.0,6,'none')]
for tf,P,w,hold,gate in CFG:
    ev=signals(P,w,hold,gate)
    M=collections.defaultdict(list)
    for t,g in ev: M[utc(t).strftime('%Y-%m')].append(g)
    print(f"\n  {tf} w{w} h{hold} gate={gate}")
    print(f"    {'month':>8} {'n':>5} {'k used':>8} {'ROI':>14} {'>1000%?':>9}")
    hist=[]
    wins=0
    for m in MON:
        g=np.array(M.get(m,[]))
        if len(hist)>=2 and len(g)>=5:
            # k = value maximising median monthly growth on PRIOR months (no peek)
            best=(-1e9,0)
            for k in np.arange(0.5,400,0.5):
                vals=[]
                ok=True
                for hg in hist:
                    x=1+np.array(hg)*k
                    if (x<=0).any(): ok=False; break
                    vals.append(np.cumprod(x)[-1])
                if not ok: break
                v=np.median(vals)
                if v>best[0]: best=(v,k)
            k=best[1]
            x=1+g*k
            roi=-100.0 if (x<=0).any() else (np.cumprod(x)[-1]-1)*100
            hit='YES' if roi>1000 else ''
            if roi>1000: wins+=1
            print(f"    {m:>8} {len(g):5d} {k:8.1f} {roi:13,.1f}% {hit:>9}")
        else:
            print(f"    {m:>8} {len(g):5d} {'(warmup)':>8}")
        if len(g)>=5: hist.append(g)
    print(f"    -> months >1000% with NO peeking: {wins}/6 tested")
