#!/usr/bin/env python3
"""EURUSD 1H FADE, k=71.5, 8 months: +1,456.66%. Is it real or curve-fit?
Tests: (1) leverage sensitivity, (2) out-of-sample split, (3) per-month,
(4) raw edge t-stat, (5) selection-noise null over the whole search."""
import sys, datetime, collections, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h()
LO,HI=1764547200,1785542400
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)

def single(panel,lo,hi,asset,flip,stop):
    keys=sorted(panel); out=[]; ts=[]
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
        out.append(r); ts.append(ek)
    return np.array(out), np.array(ts)

r,ts = single(p1,LO,HI,'eur',True,0.0)
print(f"EURUSD 1H FADE, no stop, {len(r)} trades")
print(f"  mean per-trade {r.mean()*100:+.5f}%  sd {r.std()*100:.5f}%  "
      f"t = {r.mean()/(r.std()/np.sqrt(len(r))):+.2f}")
print(f"  win rate {(r>0).mean()*100:.2f}%")
print()
print("(1) LEVERAGE SENSITIVITY - a real edge degrades smoothly; a fit spikes")
print(f"  {'k':>7} {'ROI':>18} {'maxDD':>9}")
for k in (10,20,40,60,70,71.5,73,80,90,100,120):
    g=1+r*k
    if (g<=0).any(): print(f"  {k:7.1f} {'WIPED':>18}"); continue
    eq=np.cumprod(g); pk=np.maximum.accumulate(eq)
    print(f"  {k:7.1f} {(eq[-1]-1)*100:17,.2f}% {((eq-pk)/pk).min()*100:8.2f}%")
print()
half=len(r)//2
print("(2) OUT-OF-SAMPLE SPLIT at k=71.5")
for lab,seg in (('first half',r[:half]),('second half',r[half:])):
    g=1+seg*71.5
    if (g<=0).any(): print(f"  {lab}: WIPED"); continue
    eq=np.cumprod(g)
    t=seg.mean()/(seg.std()/np.sqrt(len(seg)))
    print(f"  {lab}: n={len(seg)} ROI={(eq[-1]-1)*100:+12,.2f}%  t={t:+.2f}")
print()
print("(3) PER MONTH at k=71.5")
lab=[utc(x).strftime('%Y-%m') for x in ts]
for m in sorted(set(lab)):
    seg=r[np.array([l==m for l in lab])]
    g=1+seg*71.5
    if (g<=0).any(): print(f"  {m}: n={len(seg):4d}  WIPED"); continue
    eq=np.cumprod(g)
    print(f"  {m}: n={len(seg):4d}  ROI={(eq[-1]-1)*100:+12,.2f}%")
print()
print("(4) SELECTION-NOISE NULL")
print("    The 1,456% came from searching 3 TFs x 3 assets x 2 dirs x 2 stops x 600 leverages.")
print("    Re-run that identical search on sign-flipped bars (preserves all structure).")
rng=np.random.default_rng(11)
def best_of_search(flipmask=None):
    bb=-1e9
    for asset in A:
        for fl in (False,True):
            for stop in (0.0,0.01):
                rr,_=single(p1,LO,HI,asset,fl,stop)
                if len(rr)==0: continue
                if flipmask is not None: rr=rr*flipmask[:len(rr)]
                for k in np.arange(0.5,300,0.5):
                    g=1+rr*k
                    if (g<=0).any(): break
                    v=(np.cumprod(g)[-1]-1)*100
                    if v>bb: bb=v
    return bb
act=best_of_search()
null=[]
n=len(r)
for _ in range(120):
    fm=rng.choice([-1.0,1.0],size=n+50)
    null.append(best_of_search(fm))
null=np.array(null)
print(f"    actual best-of-search : {act:,.2f}%")
print(f"    null median {np.median(null):,.2f}%   95th pct {np.percentile(null,95):,.2f}%   max {null.max():,.2f}%")
p=(null>=act).mean()
print(f"    p = {p:.3f}  ->  {'REAL' if p<0.05 else 'INDISTINGUISHABLE FROM SELECTION NOISE'}")
