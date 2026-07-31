"""THE decisive curve: for a given directional accuracy, what is the MAX monthly ROI
achievable while keeping maxDD < 5%? Uses REAL 4H bar magnitudes. Then mark where
honest measured accuracy sits, and where the 700% goal sits."""
import numpy as np, math
from research.data import panels
P=panels()
rng=np.random.default_rng(5)
d=P['H4']; r=((d['C']-d['O'])/d['O'])
b=r.mean(1)                      # real basket bar magnitudes
BARS_PER_MO=105
COST=0.00004                     # blended round-trip, fraction of notional

def sim(acc,k,trials=300):
    mos=[];dds=[]
    for _ in range(trials):
        idx=rng.integers(0,len(b),BARS_PER_MO)
        mag=b[idx]
        correct=rng.random(BARS_PER_MO)<acc
        pnl=np.where(correct,np.abs(mag),-np.abs(mag))*k - COST*k
        eq=np.cumprod(1+pnl)
        mos.append(eq[-1]-1)
        pk=np.maximum.accumulate(eq); dds.append(((eq-pk)/pk).min())
    return np.median(mos), np.percentile(dds,5)   # 5th pct DD = bad-case

print(f"{'accuracy':>9} {'max k @DD<5%':>13} {'monthly ROI':>14}")
rows=[]
for acc in (0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95,0.98,1.00):
    bestk=0;bestm=-1
    for k in np.concatenate([np.arange(0.1,10,0.1),np.arange(10,200,2.0)]):
        mo,dd=sim(acc,k)
        if dd>-0.05: 
            if mo>bestm: bestm,bestk=mo,k
        else:
            if acc<1.0: break
    rows.append((acc,bestk,bestm))
    print(f"{acc*100:8.0f}% {bestk:13.1f} {bestm*100:+13.1f}%")

print("\nWHERE WE ACTUALLY ARE:")
print("  honest leak-free measured accuracy (best of all models/timeframes): ~55%")
print("  -> supported monthly ROI at DD<5%:", end=' ')
mo,_=sim(0.55,[x[1] for x in rows if x[0]==0.55][0]); print(f"{mo*100:+.2f}%")
print("\nACCURACY REQUIRED TO HIT +700%/MONTH AT DD<5%:")
for acc,k,mo in rows:
    if mo>=7.0:
        print(f"  >= {acc*100:.0f}% directional accuracy (k={k:.0f}x)"); break
else:
    print("  NOT REACHED even at 100% accuracy within tested size range")
