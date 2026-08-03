#!/usr/bin/env python3
"""EXTRACT THE DATA I NEVER USED.

I have only ever used: close-open (direction) and high-low (range).
Every bar contains MUCH more that I discarded:

INVISIBLE  : the path inside the bar - where did it open vs close vs extremes
HIDDEN     : which asset hit its extreme FIRST (implied by wick asymmetry)
SCATTERED  : information spread across 3 assets that is meaningless alone
NOISY      : the gap between bars (I only ever used within-bar)
DISREGARDED: upper vs lower wick, body-to-range ratio, close location

Build every one of these as a PREDICTIVE feature and test it properly.
"""
import sys, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
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

def feats(P):
    """Every layer of information in the bar. All CAUSAL (bar i and earlier)."""
    ks=sorted(P); out=[]
    for i in range(2,len(ks)-1):
        b=P[ks[i]]; pv=P[ks[i-1]]; nx=P[ks[i+1]]
        f={}
        for a in A:
            o,h,l,c=b[a]['open'],b[a]['high'],b[a]['low'],b[a]['close']
            rng=max(h-l,1e-12)
            f[f'body_{a}']=(c-o)/o                      # visible (used)
            f[f'uw_{a}']=(h-max(o,c))/o                 # DISREGARDED upper wick
            f[f'lw_{a}']=(min(o,c)-l)/o                 # DISREGARDED lower wick
            f[f'clv_{a}']=((c-l)-(h-c))/rng             # INVISIBLE close location
            f[f'br_{a}']=abs(c-o)/rng                   # INVISIBLE body/range
            f[f'gap_{a}']=(o-pv[a]['close'])/pv[a]['close']  # NOISY overnight gap
            f[f'wskew_{a}']=((h-max(o,c))-(min(o,c)-l))/rng  # HIDDEN wick skew
        # SCATTERED: cross-asset structure meaningless per-asset
        f['clv_disp']=np.std([f[f'clv_{a}'] for a in A])
        f['clv_mean']=np.mean([f[f'clv_{a}'] for a in A])
        f['wskew_mean']=np.mean([f[f'wskew_{a}'] for a in A])
        f['br_mean']=np.mean([f[f'br_{a}'] for a in A])
        f['gap_mean']=np.mean([f[f'gap_{a}'] for a in A])
        f['body_disp']=np.std([f[f'body_{a}'] for a in A])
        # target: next bar basket move
        f['fwd']=np.mean([(nx[a]['close']-nx[a]['open'])/nx[a]['open'] for a in A])
        f['t']=ks[i]
        out.append(f)
    return out

print("="*100)
print("LAYER-BY-LAYER: does each hidden feature predict NEXT-BAR DIRECTION?")
print("="*100)
for tf in ('DAILY','4H','1H'):
    R=feats(PAN[tf])
    fwd=np.array([r['fwd'] for r in R])
    print(f"\n--- {tf}  n={len(R)} ---")
    print(f"  {'feature':<16} {'layer':<14} {'IC (corr)':>10} {'t':>7} {'sign-acc':>9}")
    rows=[]
    for k,layer in (('clv_mean','INVISIBLE'),('wskew_mean','HIDDEN'),('clv_disp','SCATTERED'),
                    ('br_mean','INVISIBLE'),('gap_mean','NOISY'),('body_disp','SCATTERED')):
        x=np.array([r[k] for r in R])
        if x.std()==0: continue
        ic=np.corrcoef(x,fwd)[0,1]
        t=ic*math.sqrt(len(x)-2)/math.sqrt(max(1-ic**2,1e-12))
        pnl=np.sign(x)*fwd
        acc=(np.sign(x)==np.sign(fwd)).mean()*100
        rows.append((abs(t),k,layer,ic,t,acc))
    rows.sort(reverse=True)
    for _,k,layer,ic,t,acc in rows:
        flag="  <-- SIGNIFICANT" if abs(t)>2.5 else ""
        print(f"  {k:<16} {layer:<14} {ic:+10.4f} {t:+7.2f} {acc:8.2f}%{flag}")
