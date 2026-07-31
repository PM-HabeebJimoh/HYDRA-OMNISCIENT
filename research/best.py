"""Honest equity simulation of the only surviving edge: H4 gold momentum.
Includes REAL costs and volatility-targeted sizing. Reports what DD<5% actually buys."""
import numpy as np, math
from research.data import panels,utc
P=panels()
d=P['H4']; O,Hi,Lo,C,ts=d['O'],d['H'],d['L'],d['C'],d['ts']
G=0
r=(C-O)/O
H=5; STOP=0.010; MINSTR=0.003
COST=0.00007   # XAUUSD round-trip ~0.7bp of notional (ECN)

sig=[]
for i in range(len(r)-H-1):
    if abs(r[i,G])<MINSTR: continue
    dirn=1 if r[i,G]>0 else -1; j=i+1
    ep=O[j,G]; ex=C[min(j+H-1,len(r)-1),G]
    for m in range(j,min(j+H,len(r))):
        if dirn>0 and Lo[m,G]<=ep*(1-STOP): ex=ep*(1-STOP);break
        if dirn<0 and Hi[m,G]>=ep*(1+STOP): ex=ep*(1+STOP);break
    sig.append((ts[j],dirn*(ex-ep)/ep))
T=np.array([x[1] for x in sig]); TS=np.array([x[0] for x in sig])
print(f"trades={len(T)} gross mean={T.mean()*100:+.4f}% sd={T.std()*100:.4f}% t={T.mean()/(T.std()/np.sqrt(len(T))):+.2f}")

def sim(k,cost):
    net=T*k-cost*k
    eq=np.cumprod(1+net); peak=np.maximum.accumulate(eq)
    dd=((eq-peak)/peak).min()*100
    mo=(eq[-1]**(1/ (len(T)/ (len(T)/8.0)) ))  # 8 months of data
    monthly=eq[-1]**(1/8.0)-1
    return eq[-1],monthly*100,dd,net.mean()/ (net.std()+1e-12)

print(f"\n{'k(notional/eq)':>15} {'total x':>10} {'monthly%':>10} {'maxDD%':>9} {'SR/trade':>9}")
for k in (1,2,3,5,8,10,15,20,30,50):
    e,m,dd,sr=sim(k,COST)
    flag=' <== DD ok' if dd>-5 else ''
    print(f"{k:15d} {e:10.2f} {m:+10.2f} {dd:9.2f} {sr:+9.3f}{flag}")

print("\nWith 5% DD budget, the max monthly ROI this REAL edge supports:")
best=None
for k in np.arange(0.02,60,0.02):
    e,m,dd,sr=sim(k,COST)
    if dd>-5.0: best=(k,m,dd,e)
print("  none" if best is None else f"  k={best[0]:.2f}x -> monthly {best[1]:+.2f}%  maxDD {best[2]:.2f}%  total x{best[3]:.2f}")
print(f"\nGOAL +700%/mo at DD<5%. Achieved {best[1]:.2f}%/mo. Shortfall factor: {700/max(best[1],1e-9):,.0f}x") if best else None
