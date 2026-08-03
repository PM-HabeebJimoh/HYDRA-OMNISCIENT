"""FULL BACKTEST - JULY 2026 ONLY - Agba Metta model with the core basket
XAU/EUR/AUD REPLACED by each of four candidate baskets.

Model rules (unchanged, exactly as src/engine.py defines them):
  STEP 1 regime from real yield  (>0.7 -> CONTRACTION -> SHORT)
  STEP 2 alignment: all 3 basket assets close in the regime direction
  STEP 3 enter NEXT session open, exit that session's close
         20% equity per trade day, split equally across the 3 assets
  Direction per the research finding: FADE (trade opposite the alignment)
         except NZD+CAD+JPY which was FOLLOW.

NOTE: xpairs files carry open/close only (no high/low), so the 1% intraday stop
cannot be evaluated. All runs are open->close, no stop. Stated, not hidden.
Costs applied per instrument.
"""
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

COST={'XAUUSD':7e-5,'XAGUSD':2.5e-4,'EURUSD':2e-5,'AUDUSD':3.5e-5,'GBPUSD':3e-5,
      'NZDUSD':5e-5,'USDCAD':4e-5,'USDCHF':4e-5,'USDJPY':3e-5,'EURGBP':4e-5}

BASKETS=[(('AUDUSD','GBPUSD','USDCAD'),True ,'FADE'),
         (('EURUSD','AUDUSD','USDCAD'),True ,'FADE'),
         (('GBPUSD','NZDUSD','USDCAD'),True ,'FADE'),
         (('NZDUSD','USDCAD','USDJPY'),False,'FOLLOW')]

def run(trip,flip,lev,risk=0.20,eq0=1e5,verbose=False):
    # sessions usable for THIS basket; include the June signal bar -> July 1 entry
    ds=sorted(d for d in D if (d.startswith('2026-06') or d.startswith('2026-07'))
              and all(s in D[d] for s in trip) and 'real_yield' in D[d])
    eq=eq0; peak=eq; log=[]; curve=[eq0]
    for i in range(len(ds)-1):
        sd,td=ds[i],ds[i+1]
        if not td.startswith('2026-07'): continue      # JULY ENTRIES ONLY
        y=D[sd].get('real_yield')
        if y is None: continue
        reg=-1 if y>0.7 else (1 if y<-0.1 else 0)
        if reg==0: continue
        if reg<0 and not all(D[sd][s]['close']<D[sd][s]['open'] for s in trip): continue
        if reg>0 and not all(D[sd][s]['close']>D[sd][s]['open'] for s in trip): continue
        side=reg*(-1 if flip else 1)
        pnl=0.0; legs=[]
        for s in trip:
            b=D[td][s]; e=b['open']; c=b['close']
            notion=eq*risk/3*lev
            r=(c-e)/e*side
            lp=r*notion-COST[s]*notion
            pnl+=lp; legs.append((s,e,c,r*100,lp))
        eq+=pnl; curve.append(eq); peak=max(peak,eq)
        log.append(dict(sig=sd,trade=td,side='LONG' if side>0 else 'SHORT',pnl=pnl,eq=eq,legs=legs))
        if eq<=0: break
    c=np.array(curve); pk=np.maximum.accumulate(c)
    dd=((c-pk)/pk).min()*100
    wins=sum(1 for x in log if x['pnl']>0)
    return dict(n=len(log),wr=wins/len(log)*100 if log else 0.0,
                ret=(eq/eq0-1)*100,dd=dd,eq=eq,log=log)

print("="*100)
print("JULY 2026 FULL BACKTEST - AGBA METTA with substituted baskets")
print("20 usable July sessions (2026-07-01 .. 2026-07-28); 2026-07-29 dropped: 4 pairs missing")
print("real yield in July stays >0.7 -> regime CONTRACTION -> base direction SHORT")
print("no 1% stop: xpairs data has no high/low. open->close only. costs included.")
print("="*100)

for trip,flip,lab in BASKETS:
    print(f"\n{'#'*100}")
    print(f"# BASKET: {' + '.join(trip)}   [{lab}]")
    print(f"{'#'*100}")
    base=run(trip,flip,1)
    print(f"alignment fired on {base['n']} July trade day(s)")
    if base['n']==0:
        print("  -> NO TRADES IN JULY 2026. All 3 assets never closed the same direction on a June/July signal bar.")
        continue
    for e in base['log']:
        print(f"\n  signal {e['sig']} -> trade {e['trade']}  {e['side']}")
        for s,o,c,rp,lp in e['legs']:
            print(f"     {s:>7} open={o:<10.5f} close={c:<10.5f} move={rp:+7.3f}%")
    print(f"\n  {'leverage':>9} {'trades':>7} {'WR':>7} {'return':>13} {'maxDD':>10} {'final equity':>15}")
    for lev in (500,100,50,25,10,5,1):
        r=run(trip,flip,lev)
        print(f"  {lev:9d} {r['n']:7d} {r['wr']:6.1f}% {r['ret']:12,.2f}% {r['dd']:9.2f}% {r['eq']:14,.0f}")
    best=None
    for lev in np.arange(0.25,200,0.25):
        r=run(trip,flip,lev)
        if r['dd']>-5.0: best=(lev,r)
        else: break
    if best:
        lev,r=best
        print(f"  max size at DD<5%: {lev:.2f}x -> July return {r['ret']:+.2f}%, DD {r['dd']:.2f}%")

print("\n"+"="*100)
print("SUMMARY - JULY 2026")
print("="*100)
print(f"{'basket':>30} {'dir':>7} {'trades':>7} {'WR':>7} {'ret@25x':>10} {'DD@25x':>9} {'max lev DD<5%':>14}")
for trip,flip,lab in BASKETS:
    r=run(trip,flip,25)
    best=None
    for lev in np.arange(0.25,200,0.25):
        rr=run(trip,flip,lev)
        if rr['dd']>-5.0: best=lev
        else: break
    nm='+'.join(s[:6] for s in trip)
    if r['n']==0:
        print(f"{nm:>30} {lab:>7} {0:7d} {'-':>7} {'-':>10} {'-':>9} {'-':>14}")
    else:
        print(f"{nm:>30} {lab:>7} {r['n']:7d} {r['wr']:6.1f}% {r['ret']:9.2f}% {r['dd']:8.2f}% {best if best else 0:13.2f}x")
