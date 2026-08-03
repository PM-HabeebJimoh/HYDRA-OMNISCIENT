"""Context for the July 2026 basket results: core basket benchmark, in-sample
status, and what a single loss would do at each leverage."""
import json,glob
import numpy as np
D={}
for dt,row in json.load(open('data/market_data_spot.json')).items(): D.setdefault(dt,{}).update(row)
NAME={'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}
for dt in list(D):
    for k,v in list(D[dt].items()):
        if k in NAME: D[dt][NAME[k]]=v
for f in glob.glob('data/raw/xpairs/*.json'):
    j=json.load(open(f))
    for i,dt in enumerate(j['dates']):
        D.setdefault(dt,{})[j['symbol']]={'open':j['o'][i],'close':j['c'][i]}
COST={'XAUUSD':7e-5,'EURUSD':2e-5,'AUDUSD':3.5e-5,'GBPUSD':3e-5,'NZDUSD':5e-5,
      'USDCAD':4e-5,'USDCHF':4e-5,'USDJPY':3e-5,'EURGBP':4e-5,'XAGUSD':2.5e-4}
def run(trip,flip,lev,risk=0.20,eq0=1e5):
    ds=sorted(d for d in D if (d.startswith('2026-06') or d.startswith('2026-07'))
              and all(s in D[d] for s in trip) and 'real_yield' in D[d])
    eq=eq0; log=[]; curve=[eq0]
    for i in range(len(ds)-1):
        sd,td=ds[i],ds[i+1]
        if not td.startswith('2026-07'): continue
        y=D[sd].get('real_yield')
        if y is None: continue
        reg=-1 if y>0.7 else (1 if y<-0.1 else 0)
        if reg==0: continue
        if reg<0 and not all(D[sd][s]['close']<D[sd][s]['open'] for s in trip): continue
        if reg>0 and not all(D[sd][s]['close']>D[sd][s]['open'] for s in trip): continue
        side=reg*(-1 if flip else 1); pnl=0.0
        for s in trip:
            b=D[td][s]; e=b['open']; notion=eq*risk/3*lev
            pnl+=((b['close']-e)/e*side)*notion-COST[s]*notion
        eq+=pnl; curve.append(eq); log.append(pnl)
        if eq<=0: break
    c=np.array(curve); pk=np.maximum.accumulate(c)
    return dict(n=len(log),ret=(eq/eq0-1)*100,dd=((c-pk)/pk).min()*100,eq=eq,
                wr=sum(1 for x in log if x>0)/len(log)*100 if log else 0)

print("CORE AGBA METTA BASKET (XAUUSD+EURUSD+AUDUSD) - JULY 2026, same conditions")
for lab,flip in (('ORIGINAL (follow)',False),('REVERSED (fade)',True)):
    r=run(('XAUUSD','EURUSD','AUDUSD'),flip,25)
    print(f"  {lab:>20} @25x: {r['n']} trades, WR {r['wr']:.0f}%, return {r['ret']:+.2f}%, DD {r['dd']:.2f}%")
r5=run(('XAUUSD','EURUSD','AUDUSD'),False,500)
print(f"  ORIGINAL @500x     : {r5['n']} trades, return {r5['ret']:+.2f}%, final ${r5['eq']:,.0f}")

print("\nWHY '199.75x at DD<5%' IS MISLEADING")
print("  Those baskets had ZERO losing days in July, so DD stayed 0% at any size.")
print("  That is a property of 1-4 lucky trades, not a risk property of the strategy.")
print("  At 500x/20% split 3 ways, ONE leg moving 1% against you = -33% of equity.")
for lev in (500,200,100,50,25):
    print(f"    lev {lev:4d}x: a single -1% adverse day on all 3 legs = {-0.20*lev*1.0:.0f}% of equity"
          f"  -> {'ACCOUNT WIPED' if 0.20*lev>=1 else 'survivable'}")

print("\nIN-SAMPLE WARNING")
print("  These 4 baskets were SELECTED by searching 196 baskets over Jan-Jul 2026.")
print("  July 2026 was INSIDE that selection window.")
print("  So these July results are IN-SAMPLE - they are part of the reason the")
print("  baskets were picked. They are NOT an independent test.")
print("\n  July trade counts: 4, 4, 3, 1. At n=1-4 no statistic is meaningful.")
