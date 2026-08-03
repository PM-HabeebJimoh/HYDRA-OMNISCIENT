#!/usr/bin/env python3
"""Finer/wider sweep: leverage 25..3000 in fine steps, plus stop variants,
plus risk fraction variants. Still live-correct, no cap."""
import sys, datetime, collections
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
MON=[('Dec25',1764547200,1767225600),('Jan26',1767225600,1769904000),('Feb26',1769904000,1772323200),
     ('Mar26',1772323200,1775001600),('Apr26',1775001600,1777593600),('May26',1777593600,1780272000),
     ('Jun26',1780272000,1782864000),('Jul26',1782864000,1785542400)]

def bt(panel,lo,hi,flip,lev,risk,stop,eq0=1e5):
    keys=sorted(panel); eq=eq0; curve=[eq0]; n=0; wins=0
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s=panel[sk]
        dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
        if not (dn or up): continue
        side=(-1 if dn else 1)*(-1 if flip else 1)
        pnl=0.0; b_=panel[ek]
        for a in A:
            b=b_[a]; e=b['open']; notion=eq*risk/3*lev
            if side<0:
                if stop:
                    sp=e*(1+stop); hit=b['high']>=sp; ex=sp if hit else b['close']
                else: ex=b['close']
                r=(e-ex)/e
            else:
                if stop:
                    sp=e*(1-stop); hit=b['low']<=sp; ex=sp if hit else b['close']
                else: ex=b['close']
                r=(ex-e)/e
            pnl+=r*notion
        eq+=pnl; n+=1
        if pnl>0: wins+=1
        curve.append(eq)
        if eq<=0: return None
    if n==0: return None
    e=np.array(curve); pk=np.maximum.accumulate(e)
    return dict(ret=(eq/eq0-1)*100,dd=((e-pk)/pk).min()*100,n=n,wr=wins/n*100)

LEVS=list(range(25,3001,25))
STOPS=(0.0,0.0025,0.005,0.0075,0.01,0.015,0.02,0.03,0.05)
RISKS=(0.20,0.40,0.60,0.80,1.00)
hits=[]; tested=0; best=(-1e9,)
for nm,lo,hi in MON:
    for tf in ('DAILY','4H','1H'):
        for flip in (False,True):
            for stop in STOPS:
                for risk in RISKS:
                    for lev in LEVS:
                        r=bt(PAN[tf],lo,hi,flip,lev,risk,stop); tested+=1
                        if r is None: continue
                        if r['ret']>best[0]: best=(r['ret'],nm,tf,flip,lev,risk,stop,r)
                        if r['ret']>1000: hits.append((r['ret'],nm,tf,flip,lev,risk,stop,r))
print(f"Configurations tested: {tested:,}")
print(f"Achieving ROI > 1000% (live-correct, no cap): {len(hits)}\n")
if hits:
    hits.sort(reverse=True)
    seen=set(); out=[]
    for h in hits:
        k=(h[1],h[2])
        if k in seen: continue
        seen.add(k); out.append(h)
    print(f"{'month':>6} {'TF':>6} {'dir':>5} {'lev':>6} {'risk':>5} {'stop':>6} {'n':>4} {'WR':>6} {'ROI':>15} {'maxDD':>9}")
    for ret,nm,tf,flip,lev,risk,stop,r in out[:30]:
        print(f"{nm:>6} {tf:>6} {'FADE' if flip else 'FOLL':>5} {lev:6d} {risk:5.2f} {stop*100:5.2f}% {r['n']:4d} {r['wr']:5.1f}% {ret:14,.2f}% {r['dd']:8.2f}%")
else:
    ret,nm,tf,flip,lev,risk,stop,r=best
    print("NONE. Global best across the entire sweep:")
    print(f"  {nm} {tf} {'FADE' if flip else 'FOLL'} lev={lev} risk={risk} stop={stop*100:.2f}%")
    print(f"  n={r['n']} WR={r['wr']:.1f}% ROI={ret:,.2f}% maxDD={r['dd']:.2f}%")
