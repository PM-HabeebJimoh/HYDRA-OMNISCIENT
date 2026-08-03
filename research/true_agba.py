#!/usr/bin/env python3
"""AGBA METTA as the USER specified it — 11 steps, no real-yield gate.

  1  Wait for candle close.
  2  Check XAUUSD, EURUSD, AUDUSD direction.
  3  All 3 close UP   -> signal LONG.
  4  All 3 close DOWN -> signal SHORT.
  5  Mixed -> skip.
  6  Enter on NEXT candle open.
  7  20% equity split across the 3 assets.
  8  500x leverage.
  9  LONG stop  = entry x 0.99
 10  SHORT stop = entry x 1.01
 11  Exit at next candle close unless stop hits first.
"""
import sys, json, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); NAME={'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}
RISK,LEV,STOP,CAP0=0.20,500,0.01,100000.0
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

def run(panel,lo,hi,gate=False):
    keys=sorted(panel); eq=CAP0; curve=[eq]; tr=[]
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s=panel[sk]
        up=all(s[a]['close']>s[a]['open'] for a in A)
        dn=all(s[a]['close']<s[a]['open'] for a in A)
        if not (up or dn): continue          # STEP 5 skip mixed
        d=1 if up else -1                    # STEPS 3,4 direction FROM ALIGNMENT
        if gate:
            y=RY.get(utc(sk).strftime('%Y-%m-%d'))
            if y is None: continue
            rd=-1 if y>0.7 else (1 if y<-0.1 else 0)
            if rd==0 or rd!=d: continue      # regime must agree
        pos=eq*RISK/3; pnl=0.0
        for a in A:
            b=panel[ek][a]; en=b['open']
            sp=en*(1-STOP) if d>0 else en*(1+STOP)
            ex,why=b['close'],'CLOSE'
            if d>0 and b['low']<=sp:  ex,why=sp,'STOP'
            if d<0 and b['high']>=sp: ex,why=sp,'STOP'
            r=(ex-en)/en if d>0 else (en-ex)/en
            pnl+=r*pos*LEV
            tr.append((NAME[a],'LONG' if d>0 else 'SHORT',utc(sk),utc(ek),en,ex,r*100,why))
        eq+=pnl; curve.append(eq)
        if eq<=0: eq=0.0; break
    c=np.array(curve); pk=np.maximum.accumulate(c)
    w=sum(1 for t in tr if t[6]>0)
    return dict(eq=eq,ret=(eq/CAP0-1)*100,n=len(tr)//3,tr=tr,
                wr=w/len(tr)*100 if tr else 0,
                L=sum(1 for t in tr if t[1]=='LONG')//3,
                S=sum(1 for t in tr if t[1]=='SHORT')//3,
                stops=sum(1 for t in tr if t[7]=='STOP'),
                dd=((c-pk)/pk).min()*100 if len(c)>1 else 0)
MON=[('Dec25',1764547200,1767225600),('Jan26',1767225600,1769904000),
     ('Feb26',1769904000,1772323200),('Mar26',1772323200,1775001600),
     ('Apr26',1775001600,1777593600),('May26',1777593600,1780272000),
     ('Jun26',1780272000,1782864000),('Jul26',1782864000,1785542400)]
print("="*104)
print("AGBA METTA — as specified (direction from ALIGNMENT) vs author's code (+ real-yield gate)")
print("="*104)
for tf in ('DAILY','4H','1H'):
    print(f"\n--- {tf} ---")
    print(f"  {'month':>6} | {'AS SPECIFIED (L+S)':>34} | {'WITH REGIME GATE (S only)':>30}")
    print(f"  {'':>6} | {'sig':>4} {'L':>3} {'S':>3} {'WR':>6} {'return':>13} | {'sig':>4} {'WR':>6} {'return':>13}")
    for nm,lo,hi in MON:
        a=run(PAN[tf],lo,hi,gate=False)
        b=run(PAN[tf],lo,hi,gate=True)
        print(f"  {nm:>6} | {a['n']:4d} {a['L']:3d} {a['S']:3d} {a['wr']:5.1f}% {a['ret']:12,.2f}% "
              f"| {b['n']:4d} {b['wr']:5.1f}% {b['ret']:12,.2f}%")
