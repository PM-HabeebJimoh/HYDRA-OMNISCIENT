"""Per-currency data inventory and QUALITY audit, 2025-2026. Check before trusting."""
import json,glob,collections,datetime
import numpy as np

D=collections.defaultdict(dict)   # date -> sym -> bar
def add(dt,sym,o,c,h=None,l=None):
    D[dt][sym]={'o':o,'c':c,'h':h,'l':l}

for f,keys in (('data/market_data_spot2025.json',None),('data/market_data_spot.json',None)):
    d=json.load(open(f))
    for dt,row in d.items():
        for a,sym in (('gold','XAUUSD'),('eur','EURUSD'),('aud','AUDUSD')):
            if a in row:
                b=row[a]; add(dt,sym,b['open'],b['close'],b.get('high'),b.get('low'))
for f in sorted(glob.glob('data/raw/xpairs/*.json')):
    j=json.load(open(f))
    for i,dt in enumerate(j['dates']): add(dt,j['symbol'],j['o'][i],j['c'][i])

SYMS=['XAUUSD','XAGUSD','EURUSD','AUDUSD','GBPUSD','NZDUSD','USDCAD','USDCHF','USDJPY','EURGBP']
print(f"{'pair':>8} {'bars':>5} {'first':>11} {'last':>11} {'2025':>5} {'2026':>5} {'flat':>5} {'dup':>4} {'|move|avg':>10} {'max':>8}")
for s in SYMS:
    ds=sorted(d for d in D if s in D[d])
    y25=sum(1 for d in ds if d.startswith('2025')); y26=sum(1 for d in ds if d.startswith('2026'))
    mv=np.array([(D[d][s]['c']-D[d][s]['o'])/D[d][s]['o'] for d in ds])
    flat=int((mv==0).sum())
    cl=[D[d][s]['c'] for d in ds]
    dup=sum(1 for i in range(1,len(cl)) if cl[i]==cl[i-1])
    print(f"{s:>8} {len(ds):5d} {ds[0]:>11} {ds[-1]:>11} {y25:5d} {y26:5d} {flat:5d} {dup:4d} "
          f"{np.abs(mv).mean()*100:9.4f}% {np.abs(mv).max()*100:7.3f}%")

print("\nWeekend bars (should be ~0 for real FX sessions):")
for s in SYMS:
    ds=[d for d in D if s in D[d]]
    we=sum(1 for d in ds if datetime.date.fromisoformat(d).weekday()>=5)
    print(f"  {s:>8} {we:3d}", end='')
    if we: print("  <-- includes weekend timestamps")
    else: print()

json.dump({d:{s:D[d][s] for s in D[d]} for d in D},open('/tmp/allpairs.json','w'))
print(f"\ntotal distinct dates: {len(D)}")
c3=[d for d in D if all(s in D[d] for s in ('XAUUSD','EURUSD','AUDUSD'))]
print(f"dates with core 3 complete (2025+2026): {len(c3)}  {min(c3)} -> {max(c3)}")
all10=[d for d in D if all(s in D[d] for s in SYMS)]
print(f"dates with ALL 10 complete: {len(all10)}  {min(all10)} -> {max(all10)}")
