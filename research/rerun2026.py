"""FULL 2026 RERUN of the Agba Metta model, exact engine rules.

STEP 1 regime from real yield  (>0.7 SHORT, <-0.1 LONG, else no trade)
STEP 2 alignment: all 3 close in the regime direction
STEP 3 enter NEXT bar open, 1% hard stop intraday, exit that bar's close
       20% equity per trade day, split equally across the 3 assets

Run ORIGINAL (as the model bets) and REVERSED (flip the trade direction).
"""
import json,glob,collections,datetime
import numpy as np

# ---------- daily panel with real yield ----------
D={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items(): D.setdefault(dt,{}).update(row)
CORE=('gold','eur','aud')
dates=sorted(d for d in D if d.startswith('2026') and all(a in D[d] for a in CORE))
print(f"2026 daily: {len(dates)} sessions  {dates[0]} -> {dates[-1]}")
ys=[D[d]['real_yield'] for d in dates if 'real_yield' in D[d]]
print(f"real yield {min(ys):.2f}..{max(ys):.2f} -> always CONTRACTION -> model direction = SHORT\n")

def bt(dates,D,assets,flip,lev,risk=0.20,stop=0.01,eq0=1e5,cap=None,cost=0.0):
    eq=eq0; peak=eq; curve=[(dates[0],eq)]; tr=[]; nstop=0
    for i in range(len(dates)-1):
        d,nd=dates[i],dates[i+1]
        if 'real_yield' in D[d]:
            y=D[d]['real_yield']
            reg=-1 if y>0.7 else (1 if y<-0.1 else 0)
        else: reg=0
        if reg==0: continue
        if reg<0 and not all(D[d][a]['close']<D[d][a]['open'] for a in assets): continue
        if reg>0 and not all(D[d][a]['close']>D[d][a]['open'] for a in assets): continue
        side=reg*(-1 if flip else 1)
        pnl=0.0
        for a in assets:
            b=D[nd][a]; e=b['open']; notion=eq*risk/len(assets)*lev
            if side<0:
                s=e*(1+stop); hit=b['high']>=s; ex=s if hit else b['close']; r=(e-ex)/e
            else:
                s=e*(1-stop); hit=b['low']<=s; ex=s if hit else b['close']; r=(ex-e)/e
            if hit: nstop+=1
            pnl+=r*notion - cost*notion
        if cap is not None and pnl<-cap*eq: pnl=-cap*eq
        eq+=pnl; tr.append(pnl)
        if eq<=0: return dict(ret=-100.,dd=-100.,n=len(tr),wr=0.,eq=0.,dead=True,curve=curve,stops=nstop)
        peak=max(peak,eq); curve.append((nd,eq))
    if not tr: return dict(ret=0.,dd=0.,n=0,wr=0.,eq=eq0,dead=False,curve=curve,stops=0)
    e=np.array([c[1] for c in curve]); pk=np.maximum.accumulate(e)
    return dict(ret=(eq/eq0-1)*100, dd=((e-pk)/pk).min()*100, n=len(tr),
                wr=sum(1 for x in tr if x>0)/len(tr)*100, eq=eq, dead=False,
                curve=curve, stops=nstop)

print("="*88)
print("FULL 2026 DAILY - ORIGINAL DIRECTION (what the model does today)")
print("="*88)
print(f"{'leverage':>9} {'trades':>7} {'winrate':>8} {'return':>16} {'maxDD':>10} {'final equity':>16}")
for lev in (500,400,100,50,25,10,5,2,1):
    r=bt(dates,D,CORE,flip=False,lev=lev)
    print(f"{lev:9d} {r['n']:7d} {r['wr']:7.1f}% {r['ret']:15,.2f}% {r['dd']:9.2f}% {r['eq']:15,.0f}")

print()
print("="*88)
print("FULL 2026 DAILY - REVERSED DIRECTION (same signal, opposite side)")
print("="*88)
print(f"{'leverage':>9} {'trades':>7} {'winrate':>8} {'return':>16} {'maxDD':>10} {'final equity':>16}")
for lev in (500,400,100,50,25,10,5,2,1):
    r=bt(dates,D,CORE,flip=True,lev=lev)
    print(f"{lev:9d} {r['n']:7d} {r['wr']:7.1f}% {r['ret']:15,.2f}% {r['dd']:9.2f}% {r['eq']:15,.0f}")
