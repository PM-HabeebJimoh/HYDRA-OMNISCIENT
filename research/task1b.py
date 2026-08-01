#!/usr/bin/env python3
"""VALIDATE the +3pp candidates. 33 tests were run, so correct for selection.
Split-half, and an empirical null that repeats the ENTIRE 33-test search."""
import sys, collections, math, datetime
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h(); p4=resample_4h(p1)
def daily(p):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%86400)
        for a in A:
            d=p[t][a]
            if a not in B[b]: B[b][a]=dict(d)
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
PAN={'DAILY':daily(p1),'4H':p4,'1H':p1}
def build(P):
    ks=sorted(P); rows=[]
    for i in range(1,len(ks)-1):
        s=P[ks[i]]; pv=P[ks[i-1]]; nx=P[ks[i+1]]
        up=all(s[a]['close']>s[a]['open'] for a in A); dn=all(s[a]['close']<s[a]['open'] for a in A)
        if not(up or dn): continue
        d=1 if up else -1
        fwd=np.mean([(nx[a]['close']-nx[a]['open'])/nx[a]['open'] for a in A])
        cp=np.mean([(s[a]['close']-s[a]['low'])/max(s[a]['high']-s[a]['low'],1e-12) for a in A])
        if d<0: cp=1-cp
        rows.append(dict(t=ks[i],d=d,fwd=fwd,cp=cp))
    return rows
rows=build(PAN['4H'])
cp_med=np.median([x['cp'] for x in rows])
sel=[x for x in rows if x['cp']<cp_med]
def acc(r): return sum(1 for x in r if x['d']*x['fwd']>0)/len(r)*100
def tst(r):
    p=np.array([x['d']*x['fwd'] for x in r]); return p.mean()/(p.std()/np.sqrt(len(p)))
print("="*94); print("CANDIDATE: 4H 'close mid-candle' filter"); print("="*94)
print(f"  full sample : {acc(sel):.2f}% (n={len(sel)}, t={tst(sel):+.2f})  vs baseline {acc(rows):.2f}%")
h=len(sel)//2
print(f"  first half  : {acc(sel[:h]):.2f}% (n={h}, t={tst(sel[:h]):+.2f})")
print(f"  second half : {acc(sel[h:]):.2f}% (n={len(sel)-h}, t={tst(sel[h:]):+.2f})")
print()
print("  MONTH BY MONTH:")
m=collections.defaultdict(list)
for x in sel: m[utc(x['t']).strftime('%Y-%m')].append(x)
for k in sorted(m):
    r=m[k]; print(f"    {k}: n={len(r):3d}  {acc(r):6.2f}%")
print()
print("="*94); print("EMPIRICAL NULL — repeat the whole 33-test search on sign-flipped data"); print("="*94)
rng=np.random.default_rng(5)
def best_of_search(flip):
    best=0
    for tf in ('DAILY','4H','1H'):
        rr=build(PAN[tf])
        if not rr: continue
        f=flip[:len(rr)]
        base=sum(1 for i,x in enumerate(rr) if x['d']*x['fwd']*f[i]>0)/len(rr)*100
        cq=np.median([x['cp'] for x in rr])
        for lab,fn in (('a',lambda x:x['cp']<cq),('b',lambda x:x['cp']>=cq),
                       ('c',lambda x:x['d']>0),('d',lambda x:x['d']<0)):
            idx=[i for i,x in enumerate(rr) if fn(x)]
            if len(idx)<25: continue
            a_=sum(1 for i in idx if rr[i]['d']*rr[i]['fwd']*f[i]>0)/len(idx)*100
            best=max(best,a_-base)
    return best
null=[best_of_search(rng.choice([-1.0,1.0],size=2000)) for _ in range(300)]
null=np.array(null); act=acc(sel)-acc(rows)
print(f"  actual best gain  = {act:+.2f}pp")
print(f"  null: median {np.median(null):+.2f}pp  95th {np.percentile(null,95):+.2f}pp  max {null.max():+.2f}pp")
print(f"  p = {(null>=act).mean():.3f}  ->  {'REAL' if (null>=act).mean()<0.05 else 'SELECTION NOISE'}")
