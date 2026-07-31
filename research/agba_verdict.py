"""The Agba Metta model's OWN logic, tested exactly as written.
Regime = CONTRACTION (always, yield 1.67-2.34) -> SHORT.
Alignment = all 3 close DOWN -> confirm.
Then: does the basket keep falling the NEXT day, as the model bets?"""
import json,glob
import numpy as np
D={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items(): D.setdefault(dt,{}).update(row)
CORE=('gold','eur','aud')
dates=sorted(d for d in D if 'real_yield' in D[d] and all(a in D[d] for a in CORE))
def dn(d,a): b=D[d][a]; return b['close']<b['open']
al=[d for d in dates[:-1] if all(dn(d,a) for a in CORE)]
print(f"Sample: {dates[0]} -> {dates[-1]}  ({len(dates)} trading days)")
print(f"Regime: real yield 1.67-2.34, ALWAYS > 0.7  -> CONTRACTION -> SHORT every day")
print(f"Alignment fires (all 3 close DOWN): {len(al)} days\n")

nxt={d:dates[i+1] for i,d in enumerate(dates[:-1])}
rows=[]
for d in al:
    nd=nxt[d]
    legs=[(D[nd][a]['open']-D[nd][a]['close'])/D[nd][a]['open'] for a in CORE]  # SHORT return
    rows.append(np.mean(legs))
R=np.array(rows)
print("THE MODEL'S BET: after all 3 fall together, they keep falling -> go SHORT next day")
print(f"  days the SHORT won : {(R>0).sum():3d} / {len(R)}  = {(R>0).mean()*100:.1f}%")
print(f"  days the SHORT lost: {(R<0).sum():3d} / {len(R)}  = {(R<0).mean()*100:.1f}%")
print(f"  average result per trade: {R.mean()*100:+.4f}%  (t = {R.mean()/(R.std()/np.sqrt(len(R))):+.2f})")
print()
print("  -> The basket goes UP more often than DOWN after alignment.")
print("     The model bets on CONTINUATION. The data shows REVERSAL.")
print()
print("THE OPPOSITE BET (buy instead of sell, same signal):")
print(f"  wins {(-R>0).mean()*100:.1f}% of days, average {-R.mean()*100:+.4f}% per trade")
print()
print("Per-asset, day after alignment (positive = fell again = model right):")
for a in CORE:
    v=np.array([(D[nxt[d]][a]['open']-D[nxt[d]][a]['close'])/D[nxt[d]][a]['open'] for d in al])
    print(f"  {a:5s}: kept falling {(v>0).mean()*100:5.1f}% of the time, avg {v.mean()*100:+.4f}%")
