#!/usr/bin/env python3
"""EXHAUSTIVE HUNT FOR ROI > 1000% UNDER LIVE-CORRECT TIMING.
Real Investing.com bars only. Signal on closed bar i -> enter bar i+1 open ->
1% stop from actual entry -> exit bar i+1 close.
Sweep: 7 months x 3 timeframes x follow/fade x leverage 100..2000 x stop on/off.
No cap anywhere (the cap is the artifact we removed)."""
import sys, json, datetime, collections
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
MON=[('Dec25',1764547200,1767225600),('Jan26',1767225600,1769904000),('Feb26',1769904000,1772323200),
     ('Mar26',1772323200,1775001600),('Apr26',1775001600,1777593600),('May26',1777593600,1780272000),
     ('Jun26',1780272000,1782864000),('Jul26',1782864000,1785542400)]

def bt(panel,lo,hi,flip,lev,risk=0.20,stop=0.01,eq0=1e5):
    keys=sorted(panel); eq=eq0; curve=[eq0]; n=0; wins=0; nstop=0
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
                sp=e*(1+stop) if stop else None
                hit=stop and b['high']>=sp; ex=sp if hit else b['close']; r=(e-ex)/e
            else:
                sp=e*(1-stop) if stop else None
                hit=stop and b['low']<=sp; ex=sp if hit else b['close']; r=(ex-e)/e
            if hit: nstop+=1
            pnl+=r*notion
        eq+=pnl; n+=1
        if pnl>0: wins+=1
        curve.append(eq)
        if eq<=0: return dict(ret=-100.,dd=-100.,n=n,wr=0.,eq=0.,stops=nstop,dead=True)
    if n==0: return dict(ret=0.,dd=0.,n=0,wr=0.,eq=eq0,stops=0,dead=False)
    e=np.array(curve); pk=np.maximum.accumulate(e)
    return dict(ret=(eq/eq0-1)*100,dd=((e-pk)/pk).min()*100,n=n,wr=wins/n*100,eq=eq,stops=nstop,dead=False)

hits=[]; tested=0
for nm,lo,hi in MON:
    for tf in ('DAILY','4H','1H'):
        for flip in (False,True):
            for stop in (0.01,0.0):
                for lev in (100,200,300,400,500,750,1000,1500,2000):
                    r=bt(PAN[tf],lo,hi,flip,lev,stop=stop); tested+=1
                    if r['ret']>1000: hits.append((r['ret'],nm,tf,'FADE' if flip else 'FOLL',lev,stop,r))
print(f"Configurations tested: {tested}")
print(f"Configurations achieving ROI > 1000%: {len(hits)}\n")
if hits:
    hits.sort(reverse=True)
    print(f"{'month':>6} {'TF':>6} {'dir':>5} {'lev':>5} {'stop':>5} {'n':>4} {'WR':>6} {'ROI':>16} {'maxDD':>9}")
    for ret,nm,tf,d,lev,stop,r in hits[:40]:
        print(f"{nm:>6} {tf:>6} {d:>5} {lev:5d} {stop*100:4.0f}% {r['n']:4d} {r['wr']:5.1f}% {ret:15,.2f}% {r['dd']:8.2f}%")
else:
    print("NONE.")
    print("\nBest result found at each month/TF (live-correct, no cap):")
    best={}
    for nm,lo,hi in MON:
        for tf in ('DAILY','4H','1H'):
            b=None
            for flip in (False,True):
                for stop in (0.01,0.0):
                    for lev in (100,200,300,400,500,750,1000,1500,2000):
                        r=bt(PAN[tf],lo,hi,flip,lev,stop=stop)
                        if b is None or r['ret']>b[0]: b=(r['ret'],flip,lev,stop,r)
            best[(nm,tf)]=b
    print(f"{'month':>6} {'TF':>6} {'best cfg':>22} {'n':>4} {'ROI':>14} {'maxDD':>9}")
    for (nm,tf),(ret,flip,lev,stop,r) in best.items():
        cfg=f"{'FADE' if flip else 'FOLL'} {lev}x stop{int(stop*100)}%"
        print(f"{nm:>6} {tf:>6} {cfg:>22} {r['n']:4d} {ret:13,.2f}% {r['dd']:8.2f}%")
