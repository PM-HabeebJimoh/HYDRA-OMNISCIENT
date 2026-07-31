"""Validate the top baskets: split-half persistence + selection-noise null.
196 baskets were searched, so the winner MUST be tested against best-of-196 noise."""
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
COST={'XAUUSD':7e-5,'XAGUSD':2.5e-4,'EURUSD':2e-5,'AUDUSD':3.5e-5,'GBPUSD':3e-5,
      'NZDUSD':5e-5,'USDCAD':4e-5,'USDCHF':4e-5,'USDJPY':3e-5,'EURGBP':4e-5}
dates=sorted(d for d in D if d.startswith('2026') and all(s in D[d] for s in SYMS))
R=np.array([[ (D[d][s]['close']-D[d][s]['open'])/D[d][s]['open'] for d in dates] for s in SYMS])
n=R.shape[1]; half=n//2
print(f"{n} sessions; TRAIN {dates[0]}..{dates[half-1]}, TEST {dates[half]}..{dates[-1]}\n")

def ev(Rm,ti,flip,lo,hi):
    sg=np.sign(Rm[ti,:]); fire=np.abs(sg.sum(0))==3
    side=np.sign(sg.sum(0))*(-1 if flip else 1)
    out=[]
    for i in range(lo,min(hi,Rm.shape[1]-1)):
        if not fire[i]: continue
        out.append(np.mean([side[i]*Rm[j,i+1]-COST[SYMS[j]] for j in ti]))
    return np.array(out)

TOP=[(('AUDUSD','GBPUSD','USDCAD'),True),(('EURUSD','AUDUSD','USDCAD'),True),
     (('GBPUSD','NZDUSD','USDCAD'),True),(('EURUSD','NZDUSD','USDCAD'),True),
     (('NZDUSD','USDCAD','USDJPY'),False),(('XAUUSD','EURUSD','AUDUSD'),True)]
print("SPLIT-HALF PERSISTENCE")
print(f"{'basket':>28} {'dir':>5} | {'TRAIN n':>8} {'WR%':>6} {'t':>6} | {'TEST n':>7} {'WR%':>6} {'t':>6}")
for trip,flip in TOP:
    ti=[SYMS.index(s) for s in trip]
    a=ev(R,ti,flip,0,half); b=ev(R,ti,flip,half,n)
    f=lambda x: (len(x),(x>0).mean()*100 if len(x) else 0, x.mean()/(x.std()/np.sqrt(len(x))) if len(x)>2 and x.std()>0 else 0)
    na,wa,ta=f(a); nb,wb,tb=f(b)
    print(f"{'+'.join(s[:6] for s in trip):>28} {'FADE' if flip else 'FOLL':>5} | {na:8d} {wa:6.1f} {ta:+6.2f} | {nb:7d} {wb:6.1f} {tb:+6.2f}")

print("\nSELECTION-NOISE NULL (200 runs; flip whole days, preserving cross-pair correlation)")
def best_t(Rm):
    b=-9
    for trip in itertools.combinations(range(10),3):
        for flip in (False,True):
            a=ev(Rm,list(trip),flip,0,Rm.shape[1]-1)
            if len(a)>=15 and a.std()>0:
                b=max(b,a.mean()/(a.std()/np.sqrt(len(a))))
    return b
act=best_t(R)
rng=np.random.default_rng(17); null=[]
for _ in range(200):
    null.append(best_t(R*rng.choice([-1,1],size=(1,n))))
null=np.array(null)
print(f"  actual best t across 196 baskets = {act:+.2f}")
print(f"  noise best t: median {np.median(null):+.2f}  95th {np.percentile(null,95):+.2f}  max {null.max():+.2f}")
p=(null>=act).mean()
print(f"  p = {p:.3f}  ->  {'REAL' if p<0.05 else 'INDISTINGUISHABLE FROM SELECTION NOISE'}")
