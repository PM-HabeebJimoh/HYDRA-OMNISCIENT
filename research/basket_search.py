"""Search EVERY 3-currency alignment basket to beat XAU/EUR/AUD.

Agba Metta structure: the 3 basket assets must ALL close the same direction
(alignment on the CLOSED signal bar) -> trade those SAME 3 assets on the next
bar, open -> close, 20% equity split equally.

Constraint honestly stated: the 7 non-core pairs have open/close only (no
high/low in the source files), so the 1% intraday stop CANNOT be evaluated for
them. To compare all baskets on equal terms every basket here is run WITHOUT the
stop (open->close). The core basket is re-checked with its stop separately.

Costs applied per instrument.
"""
import json,glob,itertools,math
import numpy as np

D={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items(): D.setdefault(dt,{}).update(row)
NAME={'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}
for dt in list(D):
    for k,v in list(D[dt].items()):
        if k in NAME: D[dt][NAME[k]]=v
for f in glob.glob('data/raw/xpairs/*.json'):
    j=json.load(open(f))
    for i,dt in enumerate(j['dates']):
        D.setdefault(dt,{})[j['symbol']]={'open':j['o'][i],'close':j['c'][i]}

SYMS=['XAUUSD','XAGUSD','EURUSD','AUDUSD','GBPUSD','NZDUSD','USDCAD','USDCHF','USDJPY','EURGBP']
COST={'XAUUSD':0.00007,'XAGUSD':0.00025,'EURUSD':0.00002,'AUDUSD':0.000035,
      'GBPUSD':0.00003,'NZDUSD':0.00005,'USDCAD':0.00004,'USDCHF':0.00004,
      'USDJPY':0.00003,'EURGBP':0.00004}
dates=sorted(d for d in D if d.startswith('2026') and all(s in D[d] for s in SYMS))
print(f"Common window (all 10 pairs): {len(dates)} sessions {dates[0]} -> {dates[-1]}\n")
R={s:np.array([(D[d][s]['close']-D[d][s]['open'])/D[d][s]['open'] for d in dates]) for s in SYMS}
S={s:np.sign(R[s]) for s in SYMS}

def evaluate(trip,flip):
    sg=np.array([S[s] for s in trip])
    fire=np.abs(sg.sum(0))==3
    side=np.sign(sg.sum(0))*(-1 if flip else 1)
    idx=np.where(fire[:-1])[0]
    if len(idx)<15: return None
    per=[]
    for i in idx:
        legs=[side[i]*R[s][i+1]-COST[s] for s in trip]
        per.append(np.mean(legs))
    a=np.array(per)
    t=a.mean()/(a.std()/np.sqrt(len(a))) if a.std()>0 else 0
    return dict(n=len(a),wr=(a>0).mean()*100,mu=a.mean()*100,t=t,r=a)

def size_at_dd(a,cap=0.05):
    best=None
    for k in np.arange(0.25,120,0.25):
        eq=np.cumprod(1+a*k)
        dd=((eq-np.maximum.accumulate(eq))/np.maximum.accumulate(eq)).min()
        if dd>-cap: best=(k,eq[-1],dd)
        else: break
    return best

res=[]
for trip in itertools.combinations(SYMS,3):
    for flip in (False,True):
        o=evaluate(trip,flip)
        if o: res.append((o['t'],trip,flip,o))
res.sort(key=lambda x:-x[0])
print(f"Baskets tested: {len(res)} (120 triplets x 2 directions)\n")
print("TOP 20 BY EDGE STRENGTH (t-stat)")
print(f"{'basket':>28} {'dir':>5} {'n':>4} {'WR%':>6} {'edge%/tr':>9} {'t':>6} {'lev@DD5%':>9} {'/month':>8}")
for t,trip,flip,o in res[:20]:
    b=size_at_dd(o['r'])
    if b:
        k,fin,dd=b; mo=(fin**(1/7.0)-1)*100
        extra=f"{k:8.1f}x {mo:+7.2f}%"
    else: extra=f"{'-':>9} {'-':>8}"
    print(f"{'+'.join(s[:6] for s in trip):>28} {'FADE' if flip else 'FOLL':>5} {o['n']:4d} {o['wr']:6.1f} {o['mu']:+9.4f} {t:+6.2f} {extra}")

# where does the current basket rank?
print("\nCURRENT AGBA METTA BASKET (XAUUSD+EURUSD+AUDUSD):")
for flip in (False,True):
    o=evaluate(('XAUUSD','EURUSD','AUDUSD'),flip)
    rank=1+sum(1 for x in res if x[0]>o['t'])
    b=size_at_dd(o['r']); mo=(b[1]**(1/7.0)-1)*100 if b else float('nan')
    print(f"  {'FADE(reversed)' if flip else 'FOLLOW(original)':>18}: n={o['n']} WR={o['wr']:.1f}% "
          f"edge={o['mu']:+.4f}% t={o['t']:+.2f}  rank {rank}/{len(res)}  "
          f"{'lev '+format(b[0],'.1f')+'x -> '+format(mo,'+.2f')+'%/mo' if b else ''}")
np.save('/tmp/basket_R.npy',np.array([R[s] for s in SYMS])); json.dump(SYMS,open('/tmp/basket_syms.json','w'))
json.dump([[list(t[1]),t[2]] for t in res[:20]],open('/tmp/top20.json','w'))
