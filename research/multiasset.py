#!/usr/bin/env python3
"""THE DECISIVE TEST: does adding genuinely different asset classes raise N_eff?
I claimed N_eff=32 was needed and unreachable on gold/eur/aud. Now I have
equities (SPX) and crypto (BTC). Measure the real correlation structure."""
import sys, json, glob, datetime, collections, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h()

# FX/metals daily closes from the 1H panel
D=collections.defaultdict(dict)
for t in sorted(p1):
    d=utc(t).strftime('%Y-%m-%d')
    for a in ('gold','eur','aud'):
        D[d][a]=p1[t][a]['close']
for f in glob.glob('data/raw/multiasset/*.json'):
    j=json.load(open(f))
    for i,d in enumerate(j['dates']): D[d][j['name']]=j['c'][i]

SY=['gold','eur','aud','SPX','BTC']
days=sorted(d for d in D if all(s in D[d] for s in SY))
print("="*92); print("MULTI-ASSET-CLASS PANEL"); print("="*92)
print(f"  common days with ALL 5 instruments: {len(days)}  {days[0]} .. {days[-1]}")
P=np.array([[D[d][s] for s in SY] for d in days])
R=np.diff(np.log(P),axis=0)
print(f"  daily log-return matrix: {R.shape}\n")

C=np.corrcoef(R.T)
print("  CORRELATION MATRIX")
print("        "+" ".join(f"{s:>7}" for s in SY))
for i,s in enumerate(SY):
    print(f"  {s:>5} "+" ".join(f"{C[i,j]:7.3f}" for j in range(len(SY))))
ev=np.linalg.eigvalsh(C)[::-1]
neff=(ev.sum()**2)/(ev**2).sum()
print(f"\n  PC1 explains {ev[0]/ev.sum()*100:.1f}%")
print(f"  N_eff = {neff:.2f}  from {len(SY)} instruments")
print()
# compare against FX-only
C3=np.corrcoef(R[:,:3].T); ev3=np.linalg.eigvalsh(C3)[::-1]
n3=(ev3.sum()**2)/(ev3**2).sum()
print(f"  FX/metals only (gold,eur,aud): N_eff = {n3:.2f} from 3")
print(f"  adding SPX + BTC             : N_eff = {neff:.2f} from 5")
print(f"  -> per-instrument efficiency {n3/3:.2f} -> {neff/5:.2f}")
print()
print("  KEY NUMBERS:")
for i,s in enumerate(SY):
    if s in ('SPX','BTC'):
        cs=[abs(C[i,j]) for j,x in enumerate(SY) if x in ('gold','eur','aud')]
        print(f"    {s} vs FX/metals: mean |corr| = {np.mean(cs):.3f}  <- {'GENUINELY UNCORRELATED' if np.mean(cs)<0.25 else 'correlated'}")

print()
print("="*92); print("WHAT THIS BUYS — Sharpe scaling"); print("="*92)
print("  SR_portfolio = SR_single x sqrt(N_eff), spec needs ann SR 13")
best_single=2.31
for lab,n in (("3 FX/metals (measured)",n3),("5 incl SPX+BTC (measured)",neff),
              ("20 instruments @ same efficiency",neff/5*20),
              ("60 instruments @ same efficiency",neff/5*60),
              ("200 instruments @ same efficiency",neff/5*200)):
    print(f"    {lab:<36} N_eff={n:6.2f}  -> portfolio SR = {best_single*math.sqrt(n):6.2f}")
need=(13/best_single)**2
print(f"\n  N_eff required for SR 13 = {need:.0f}")
print(f"  instruments needed at measured efficiency {neff/5:.2f} = {need/(neff/5):.0f}")
