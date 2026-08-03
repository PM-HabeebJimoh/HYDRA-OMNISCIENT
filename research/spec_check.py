#!/usr/bin/env python3
"""Does the model take direction from REAL YIELD, or from the ALIGNMENT ITSELF?

User's stated spec (verbatim, 11 steps):
  1 Wait for candle close.
  2 Check XAUUSD, EURUSD, AUDUSD direction.
  3 If all 3 close UP from their opens, signal LONG.
  4 If all 3 close DOWN from their opens, signal SHORT.
  5 If mixed, skip.
  6 Enter on next candle open.
  ...
-> DIRECTION COMES FROM THE ALIGNMENT. There is no real-yield step.

Author's config adds a regime gate. Real yield is 1.67-2.34 (always >0.7),
so that gate forces CONTRACTION/SHORT and DELETES every LONG signal.
Quantify exactly what the gate removes."""
import sys, json, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h(); p4=resample_4h(p1)
def daily(p):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%86400)
        for a in A:
            d=p[t][a]
            if a not in B[b]: B[b][a]=dict(d)
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
PAN={'DAILY':daily(p1),'4H':p4,'1H':p1}
RY={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items():
        if 'real_yield' in row: RY[dt]=row['real_yield']
ys=[v for v in RY.values()]
print("="*92)
print("STEP 1 — what does the real-yield gate actually do?")
print("="*92)
print(f"  real yield range across the whole sample: {min(ys):.2f} to {max(ys):.2f}")
print(f"  days above 0.7 (CONTRACTION/SHORT): {sum(1 for v in ys if v>0.7)} of {len(ys)}")
print(f"  days below -0.1 (EXPANSION/LONG)  : {sum(1 for v in ys if v<-0.1)} of {len(ys)}")
print("  -> the gate is a CONSTANT. It never selects; it only deletes LONGs.\n")
print("="*92)
print("STEP 2 — how many signals does each version produce?")
print("="*92)
print(f"{'TF':>6} {'all-3 aligned':>14} {'UP (LONG)':>11} {'DOWN (SHORT)':>13} {'kept by gate':>13} {'DELETED':>9}")
for tf,P in PAN.items():
    ks=sorted(P); up=dn=0
    for k in ks:
        b=P[k]
        if all(b[a]['close']>b[a]['open'] for a in A): up+=1
        elif all(b[a]['close']<b[a]['open'] for a in A): dn+=1
    print(f"{tf:>6} {up+dn:14d} {up:11d} {dn:13d} {dn:13d} {up:9d}")
print("\n  The regime gate throws away every LONG signal the alignment finds.")
