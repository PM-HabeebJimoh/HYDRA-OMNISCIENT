"""Does a WIDER instrument set buy independent bets? Measure N_eff honestly.
Daily o->c, 2026, 10 instruments, 100% real Investing.com."""
import json,glob,collections
import numpy as np
from research.data import panels

# xpairs: daily open/close only
X=collections.defaultdict(dict)
for f in sorted(glob.glob('data/raw/xpairs/*.json')):
    d=json.load(open(f))
    for i,dt in enumerate(d['dates']):
        X[dt][d['symbol']]={'o':d['o'][i],'c':d['c'][i]}

# core 3 from 1H-derived daily panel
P=panels()['D1']
import datetime
core={}
for i,t in enumerate(P['ts']):
    dt=datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc).strftime('%Y-%m-%d')
    core[dt]={a:{'o':P['O'][i,j],'c':P['C'][i,j]} for j,a in enumerate(('XAUUSD','EURUSD','AUDUSD'))}

syms=['XAUUSD','EURUSD','AUDUSD','GBPUSD','NZDUSD','USDCAD','USDCHF','USDJPY','EURGBP','XAGUSD']
dates=sorted(set(X)&set(core))
rows=[]; keep=[]
for dt in dates:
    m={**core[dt],**X[dt]}
    if all(s in m for s in syms):
        rows.append([ (m[s]['c']-m[s]['o'])/m[s]['o'] for s in syms]); keep.append(dt)
R=np.array(rows)
print(f"aligned daily bars: {len(R)}  {keep[0]} .. {keep[-1]}")
print(f"instruments: {syms}\n")

C=np.corrcoef(R.T)
print("correlation matrix (o->c daily):")
print("         "+" ".join(f"{s[:6]:>7}" for s in syms))
for i,s in enumerate(syms):
    print(f"{s:>8} "+" ".join(f"{C[i,j]:7.2f}" for j in range(len(syms))))

def neff(Rm):
    w=np.ones(Rm.shape[1])/Rm.shape[1]
    sd=Rm.std(0); port=(Rm*w).sum(1).std(); naive=np.sqrt(((w*sd)**2).sum())
    return (naive/port)**2

print(f"\nN_eff, equal weight, all 10        = {neff(R):.2f}")
print(f"N_eff, core 3 (XAU/EUR/AUD)        = {neff(R[:,:3]):.2f}")
# USD-neutral: flip USDxxx so all are 'USD down' bets
sgn=np.array([1,1,1,1,1,-1,-1,-1,0,1.0])
print(f"\nEigenvalue spectrum (variance share of each principal component):")
ev=np.linalg.eigvalsh(C)[::-1]
for i,e in enumerate(ev): print(f"  PC{i+1}: {e/ev.sum()*100:5.1f}%")
print(f"  -> PC1 alone explains {ev[0]/ev.sum()*100:.1f}% : ONE dollar factor dominates.")
print(f"  participation ratio N_eff = {(ev.sum()**2)/ (ev**2).sum():.2f}")
np.save('/tmp/R.npy',R); json.dump({'syms':syms,'dates':keep},open('/tmp/Rmeta.json','w'))
