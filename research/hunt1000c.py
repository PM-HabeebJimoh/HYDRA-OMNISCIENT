#!/usr/bin/env python3
"""Last avenues to >1000% live-correct:
 (a) COMPOUND across all 8 months (Dec25-Jul26) at one fixed config
 (b) all 4 substitute baskets on daily
 (c) per-asset single-instrument runs
 (d) hindsight-optimal leverage per month, compounded"""
import sys, json, glob, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
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
LO,HI=1764547200,1785542400

def barret(panel,lo,hi,flip,stop):
    keys=sorted(panel); out=[]
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s=panel[sk]
        dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
        if not (dn or up): continue
        side=(-1 if dn else 1)*(-1 if flip else 1); legs=[]
        for a in A:
            b=panel[ek][a]; e=b['open']
            if side<0:
                sp=e*(1+stop); ex=sp if (stop and b['high']>=sp) else b['close']; r=(e-ex)/e
            else:
                sp=e*(1-stop); ex=sp if (stop and b['low']<=sp) else b['close']; r=(ex-e)/e
            legs.append(r)
        out.append(np.mean(legs))
    return np.array(out)

print("(a) FULL 8-MONTH COMPOUND, Dec2025->Jul2026, single fixed config, leverage optimised")
print(f"{'TF':>6} {'dir':>5} {'stop':>6} {'n':>5} {'best k':>8} {'8-mo ROI':>16} {'maxDD':>9}")
gbest=(-1e9,)
for tf in ('DAILY','4H','1H'):
    for flip in (False,True):
        for stop in (0.0,0.005,0.01,0.02):
            r=barret(PAN[tf],LO,HI,flip,stop)
            if len(r)==0: continue
            b=None
            for k in np.arange(0.5,300,0.5):
                g=1+r*k
                if (g<=0).any(): break
                eq=np.cumprod(g); pk=np.maximum.accumulate(eq)
                ret=(eq[-1]-1)*100
                if b is None or ret>b[0]: b=(ret,k,((eq-pk)/pk).min()*100)
            if b:
                if b[0]>gbest[0]: gbest=(b[0],tf,flip,stop,b[1],b[2],len(r))
                print(f"{tf:>6} {'FADE' if flip else 'FOLL':>5} {stop*100:5.2f}% {len(r):5d} {b[1]:8.1f} {b[0]:15,.2f}% {b[2]:8.2f}%")
print(f"\n  BEST 8-month compound: {gbest[0]:,.2f}%  ({gbest[1]} {'FADE' if gbest[2] else 'FOLL'})")

print("\n(b) SINGLE-INSTRUMENT (no basket) - does concentrating in gold help?")
def single(panel,lo,hi,asset,flip,stop):
    keys=sorted(panel); out=[]
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s=panel[sk]
        dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
        if not (dn or up): continue
        side=(-1 if dn else 1)*(-1 if flip else 1)
        b=panel[ek][asset]; e=b['open']
        if side<0:
            sp=e*(1+stop); ex=sp if (stop and b['high']>=sp) else b['close']; r=(e-ex)/e
        else:
            sp=e*(1-stop); ex=sp if (stop and b['low']<=sp) else b['close']; r=(ex-e)/e
        out.append(r)
    return np.array(out)
print(f"{'TF':>6} {'asset':>6} {'dir':>5} {'n':>5} {'best k':>8} {'8-mo ROI':>16}")
sbest=(-1e9,)
for tf in ('DAILY','4H','1H'):
    for a in A:
        for flip in (False,True):
            for stop in (0.0,0.01):
                r=single(PAN[tf],LO,HI,a,flip,stop)
                if len(r)==0: continue
                b=None
                for k in np.arange(0.5,300,0.5):
                    g=1+r*k
                    if (g<=0).any(): break
                    eq=np.cumprod(g); ret=(eq[-1]-1)*100
                    if b is None or ret>b[0]: b=(ret,k)
                if b and b[0]>sbest[0]: sbest=(b[0],tf,a,flip,b[1],len(r))
ret,tf,a,flip,k,n=sbest
print(f"{tf:>6} {a:>6} {'FADE' if flip else 'FOLL':>5} {n:5d} {k:8.1f} {ret:15,.2f}%   <- best single instrument")

print("\n(c) HINDSIGHT-PERFECT: pick the best month/TF/dir/leverage separately for EACH month,")
print("    then compound those 8 best months together (impossible live - upper bound only)")
MON=[('Dec25',1764547200,1767225600),('Jan26',1767225600,1769904000),('Feb26',1769904000,1772323200),
     ('Mar26',1772323200,1775001600),('Apr26',1775001600,1777593600),('May26',1777593600,1780272000),
     ('Jun26',1780272000,1782864000),('Jul26',1782864000,1785542400)]
tot=1.0
for nm,lo,hi in MON:
    best=None
    for tf in ('DAILY','4H','1H'):
        for flip in (False,True):
            for stop in (0.0,0.005,0.01,0.02):
                r=barret(PAN[tf],lo,hi,flip,stop)
                if len(r)==0: continue
                for k in np.arange(0.5,300,0.5):
                    g=1+r*k
                    if (g<=0).any(): break
                    eq=np.cumprod(g)[-1]
                    if best is None or eq>best[0]: best=(eq,tf,flip,k)
    if best:
        tot*=best[0]
        print(f"   {nm}: best {best[1]:>5} k={best[3]:.1f} -> x{best[0]:.3f}")
print(f"\n   COMPOUNDED 8 best months with FULL HINDSIGHT: {(tot-1)*100:,.2f}%")
print(f"   (this is unattainable live - it requires knowing each month's best config in advance)")
