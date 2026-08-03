#!/usr/bin/env python3
"""THE REAL AGBA METTA — 4 steps, signal candle SEPARATE from entry candle.

  STEP 1  REGIME    real yield >0.7 = CONTRACTION/SHORT
                              <-0.1 = EXPANSION/LONG
                              else  = STABILITY/no trade
  STEP 2  SIGNAL    candle i CLOSES. All 3 close in the regime direction.
                    mixed -> no signal.
  STEP 3  ENTRY     candle i+1 OPEN.   <-- SEPARATE CANDLE
  STEP 4  EXIT      candle i+1 CLOSE, unless the 1% stop hits intraday.

  Sizing 20% equity, split /3, 500x. Stop 1% from ACTUAL entry price.
"""
import sys, json, glob, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); NAME={'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}
RISK,LEV,STOP,CAP0=0.20,500,0.01,100000.0
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
RY={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items():
        if 'real_yield' in row: RY[dt]=row['real_yield']
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

def regime(y):
    if y is None: return 'NO_YIELD',0
    if y>0.7:  return 'CONTRACTION',-1
    if y<-0.1: return 'EXPANSION',1
    return 'STABILITY',0

def run(panel,lo=None,hi=None,same_candle=False):
    keys=sorted(panel); eq=CAP0; curve=[eq]; trades=[]
    for i in range(len(keys)-1):
        sk=keys[i]                     # SIGNAL candle
        ek=keys[i] if same_candle else keys[i+1]   # ENTRY candle
        if lo is not None and not (lo<=ek<hi): continue
        reg,d=regime(RY.get(utc(sk).strftime('%Y-%m-%d')))
        if d==0: continue
        s=panel[sk]
        # STEP 2: alignment on the CLOSED signal candle
        if d==-1 and not all(s[a]['close']<s[a]['open'] for a in A): continue
        if d== 1 and not all(s[a]['close']>s[a]['open'] for a in A): continue
        pos=eq*RISK/3; pnl=0.0
        for a in A:
            b=panel[ek][a]; en=b['open']
            sp=en*(1+STOP) if d==-1 else en*(1-STOP)
            ex,why=b['close'],'CLOSE'
            if d==-1 and b['high']>=sp: ex,why=sp,'STOP'
            if d== 1 and b['low'] <=sp: ex,why=sp,'STOP'
            r=(en-ex)/en if d==-1 else (ex-en)/en
            pnl+=r*pos*LEV
            trades.append((NAME[a],utc(sk),utc(ek),en,ex,r*100,why))
        eq+=pnl; curve.append(eq)
        if eq<=0: eq=0.0; break
    c=np.array(curve); pk=np.maximum.accumulate(c)
    wins=sum(1 for t in trades if t[5]>0)
    return dict(eq=eq,ret=(eq/CAP0-1)*100,n=len(trades)//3,
                aw=wins/len(trades)*100 if trades else 0,
                stops=sum(1 for t in trades if t[6]=='STOP'),
                dd=((c-pk)/pk).min()*100,trades=trades)

JUL=(int(datetime.datetime(2026,7,1,tzinfo=datetime.timezone.utc).timestamp()),
     int(datetime.datetime(2026,8,1,tzinfo=datetime.timezone.utc).timestamp()))
print("="*100)
print("THE REAL AGBA METTA — signal candle i, entry candle i+1")
print("="*100)
print(f"{'TF':>6} {'timing':>22} {'signals':>8} {'asset_WR':>9} {'stops':>6} {'return':>16} {'maxDD':>10}")
for tf in ('DAILY','4H','1H'):
    for sc,lab in ((True,'same candle (code)'),(False,'NEXT candle (model)')):
        r=run(PAN[tf],*JUL,same_candle=sc)
        print(f"{tf:>6} {lab:>22} {r['n']:8d} {r['aw']:8.1f}% {r['stops']:6d} {r['ret']:15,.2f}% {r['dd']:9.2f}%")
    print()
print("="*100)
print("THE REAL MODEL, JULY 2026 DAILY — every trade")
print("="*100)
r=run(PAN['DAILY'],*JUL,same_candle=False)
print(f"  {'asset':<8}{'signal candle':>13}{'entry candle':>14}{'entry':>11}{'exit':>11}{'move':>9}  {'exit'}")
for t in r['trades']:
    print(f"  {t[0]:<8}{t[1].strftime('%Y-%m-%d'):>13}{t[2].strftime('%Y-%m-%d'):>14}"
          f"{t[3]:>11.5f}{t[4]:>11.5f}{t[5]:>+8.3f}%  {t[6]}")
print(f"\n  {r['n']} signals -> {len(r['trades'])} asset trades, {r['stops']} stopped")
print(f"  final ${r['eq']:,.2f}  return {r['ret']:+.2f}%  maxDD {r['dd']:.2f}%")
