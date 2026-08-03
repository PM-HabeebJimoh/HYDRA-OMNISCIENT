"""THE TRUE AGBA METTA on full 2026: regime filter ON (yield>0.7 -> SHORT only),
alignment must confirm, enter next bar open, 1% stop, exit close. With costs.
Reported original vs reversed, plus monthly breakdown."""
import json
import numpy as np
D={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items(): D.setdefault(dt,{}).update(row)
A=('gold','eur','aud')
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
dates=sorted(d for d in D if d.startswith('2026') and all(a in D[d] for a in A) and 'real_yield' in D[d])

def bt(flip,lev,risk=0.20,stop=0.01,eq0=1e5,costs=True,ds=None):
    ds=ds or dates; eq=eq0; curve=[]; tr=[]; log=[]
    for i in range(len(ds)-1):
        d,nd=ds[i],ds[i+1]
        y=D[d]['real_yield']; reg=-1 if y>0.7 else (1 if y<-0.1 else 0)
        if reg==0: continue
        if reg<0 and not all(D[d][a]['close']<D[d][a]['open'] for a in A): continue
        if reg>0 and not all(D[d][a]['close']>D[d][a]['open'] for a in A): continue
        side=reg*(-1 if flip else 1); pnl=0.0
        for a in A:
            b=D[nd][a]; e=b['open']; notion=eq*risk/3*lev
            if side<0:
                st=e*(1+stop); hit=b['high']>=st; ex=st if hit else b['close']; r=(e-ex)/e
            else:
                st=e*(1-stop); hit=b['low']<=st; ex=st if hit else b['close']; r=(ex-e)/e
            pnl+=r*notion-(COST[a]*notion if costs else 0)
        eq+=pnl; tr.append(pnl); curve.append(eq); log.append((nd,pnl,eq))
        if eq<=0: return dict(ret=-100.,dd=-100.,n=len(tr),wr=0.,eq=0.,log=log)
    if not tr: return dict(ret=0.,dd=0.,n=0,wr=0.,eq=eq0,log=[])
    e=np.array(curve); pk=np.maximum.accumulate(np.concatenate([[eq0],e]))[1:]
    return dict(ret=(eq/eq0-1)*100,dd=((e-pk)/pk).min()*100,n=len(tr),
                wr=sum(1 for x in tr if x>0)/len(tr)*100,eq=eq,log=log)

print(f"TRUE AGBA METTA - full 2026: {len(dates)} sessions, {dates[0]} -> {dates[-1]}")
print(f"regime: real yield always >0.7 -> SHORT-only, alignment must confirm\n")
r0=bt(False,1); print(f"aligned trade days in 2026: {r0['n']}\n")

print("="*90)
print(f"{'':>10} {'ORIGINAL (SHORT the fall)':>36} | {'REVERSED (BUY the fall)':>32}")
print(f"{'leverage':>10} {'WR':>7} {'return':>14} {'maxDD':>10} | {'WR':>7} {'return':>13} {'maxDD':>9}")
print("="*90)
for lev in (500,400,100,50,25,10,7,5,3,2,1):
    a=bt(False,lev); b=bt(True,lev)
    print(f"{lev:10d} {a['wr']:6.1f}% {a['ret']:13,.2f}% {a['dd']:9.2f}% | {b['wr']:6.1f}% {b['ret']:12,.2f}% {b['dd']:8.2f}%")

print("\nBEST SIZE AT DD<5% (reversed):")
best=None
for lev in np.arange(0.5,60,0.25):
    r=bt(True,lev)
    if r['dd']>-5.0: best=(lev,r)
lev,r=best; mo=(1+r['ret']/100)**(1/7.0)-1
print(f"  lev {lev:.2f}x -> return {r['ret']:+.2f}%  DD {r['dd']:.2f}%  WR {r['wr']:.1f}%  = {mo*100:+.2f}%/month")

print("\nMONTH BY MONTH 2026 (reversed, lev=25x):")
r=bt(True,25)
import collections
m=collections.defaultdict(lambda:[0,0.0,1e5])
prev=1e5
for dt,pnl,eq in r['log']:
    k=dt[:7]; m[k][0]+=1; m[k][1]+=pnl
print(f"  {'month':>8} {'trades':>7} {'P&L':>14}")
for k in sorted(m): print(f"  {k:>8} {m[k][0]:7d} {m[k][1]:13,.0f}")

print("\nSANITY: original direction at the model's own 500x")
a=bt(False,500)
print(f"  {a['n']} trades, win rate {a['wr']:.1f}%, return {a['ret']:.2f}%, final equity ${a['eq']:,.0f}")
