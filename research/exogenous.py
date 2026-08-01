#!/usr/bin/env python3
"""OFF-CHART DATA — does information the price does NOT contain predict direction?

VIX      : equity fear      -> risk-off buys USD, sells AUD
DXY      : broad dollar     -> the actual driver of all 3 assets
HYSPREAD : credit stress    -> leads FX by hours/days
CURVE    : 10y-2y slope     -> growth expectations

CRITICAL: all are DAILY, published with a lag. To avoid look-ahead I use the
value from the PREVIOUS day only (t-1), predicting day t.
"""
import sys, json, glob, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h
A=('gold','eur','aud')
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h()
# daily bars for the 3 assets
D=collections.defaultdict(dict)
for t in sorted(p1):
    d=utc(t).strftime('%Y-%m-%d')
    for a in A:
        b=p1[t][a]
        if a not in D[d]: D[d][a]=dict(b)
        else:
            x=D[d][a]; x['high']=max(x['high'],b['high']); x['low']=min(x['low'],b['low']); x['close']=b['close']
D={d:v for d,v in D.items() if len(v)==3}
M={}
for f in glob.glob('data/raw/macro/*.json'):
    j=json.load(open(f)); M[j['name']]=dict(zip(j['dates'],j['v']))
print("="*100)
print("OFF-CHART EXOGENOUS DATA vs THE CHART")
print("="*100)
days=sorted(set(D) & set.intersection(*[set(v) for v in M.values()]))
print(f"  common days with price + VIX + DXY + HYSPREAD + CURVE : {len(days)}")
print(f"  {days[0]} .. {days[-1]}\n")
# build lagged features (t-1) -> target day t
X=[];Y=[];YR=[];T=[]
for i in range(2,len(days)):
    d0,d1,d2=days[i-2],days[i-1],days[i]
    row=[]
    for k in ('VIX','DXY','HYSPREAD','CURVE'):
        v1,v0=M[k][d1],M[k][d0]
        row.append((v1-v0)/abs(v0) if v0 else 0.0)   # 1-day change, known at close of d1
        row.append(v1)                                # level
    # cross terms: the SCATTERED logic
    row.append(((M['VIX'][d1]-M['VIX'][d0])/M['VIX'][d0])*((M['DXY'][d1]-M['DXY'][d0])/M['DXY'][d0])*1e4)
    row.append(((M['HYSPREAD'][d1]-M['HYSPREAD'][d0]))*((M['VIX'][d1]-M['VIX'][d0])))
    b=D[d2]
    X.append(row)
    Y.append(np.mean([(b[a]['close']-b[a]['open'])/b[a]['open'] for a in A]))
    YR.append(np.mean([(b[a]['high']-b[a]['low'])/b[a]['open'] for a in A]))
    T.append(d2)
X=np.array(X);Y=np.array(Y);YR=np.array(YR)
print(f"  feature matrix {X.shape}, target = NEXT day basket return\n")
names=['dVIX','VIX','dDXY','DXY','dHY','HY','dCURVE','CURVE','dVIXxdDXY','dHYxdVIX']
print("  SINGLE-FEATURE PREDICTIVE POWER (all lagged, no look-ahead)")
print(f"  {'feature':<12} {'IC vs direction':>17} {'t':>7} {'IC vs range':>13} {'t':>7}")
for j,nm in enumerate(names):
    x=X[:,j]
    if x.std()==0: continue
    ic=np.corrcoef(x,Y)[0,1]; t=ic*math.sqrt(len(x)-2)/math.sqrt(max(1-ic**2,1e-12))
    ic2=np.corrcoef(x,YR)[0,1]; t2=ic2*math.sqrt(len(x)-2)/math.sqrt(max(1-ic2**2,1e-12))
    f1="*" if abs(t)>2 else " "; f2="*" if abs(t2)>2 else " "
    print(f"  {nm:<12} {ic:+16.4f}{f1} {t:+7.2f} {ic2:+12.4f}{f2} {t2:+7.2f}")
