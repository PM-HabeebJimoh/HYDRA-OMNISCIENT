#!/usr/bin/env python3
"""THE VOLATILITY RISK PREMIUM TRADE — my forecast vs the market's forecast.

GVZ = options market's implied vol for gold (annualised %).
I can forecast realised range with R2 up to 32%.

The trade that pays for a range forecast:
  my_forecast > implied  -> market underprices movement -> BUY volatility
  my_forecast < implied  -> market overprices movement  -> SELL volatility

With spot I proxy long-vol via a bracket, short-vol via fading the bracket.
CRITICAL: GVZ is known at prior close -> no look-ahead.
"""
import sys, json, glob, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h
A=('gold','eur','aud'); utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h()
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
days=sorted(set(D)&set(M['GVZ']))
print("="*100); print("IMPLIED vs REALISED — gold"); print("="*100)
print(f"  days with gold price + GVZ implied vol: {len(days)}")
# realised daily range as annualised vol proxy
rv=[];iv=[]
for d in days:
    b=D[d]['gold']
    r=(b['high']-b['low'])/b['open']
    rv.append(r/1.13*math.sqrt(252)*100)   # Parkinson -> annualised %
    iv.append(M['GVZ'][d])
rv=np.array(rv); iv=np.array(iv)
print(f"  mean realised (Parkinson, ann) = {rv.mean():.2f}%")
print(f"  mean implied  (GVZ)            = {iv.mean():.2f}%")
print(f"  MEAN VRP (implied - realised)  = {iv.mean()-rv.mean():+.2f}%  <- the premium sellers earn")
print(f"  days implied > realised        = {(iv>rv).mean()*100:.1f}%")
print()
print("="*100); print("CAN I BEAT THE OPTIONS MARKET'S FORECAST?"); print("="*100)
# next-day realised vs today's implied, and vs my simple forecast
nxt_rv=rv[1:]; today_iv=iv[:-1]; today_rv=rv[:-1]
ic_iv=np.corrcoef(today_iv,nxt_rv)[0,1]
ic_rv=np.corrcoef(today_rv,nxt_rv)[0,1]
n=len(nxt_rv)
t=lambda ic: ic*math.sqrt(n-2)/math.sqrt(max(1-ic**2,1e-12))
print(f"  predicting NEXT-DAY realised range:")
print(f"    market's implied vol (GVZ)  IC={ic_iv:+.4f}  t={t(ic_iv):+6.2f}  R2={ic_iv**2*100:5.2f}%")
print(f"    today's realised range      IC={ic_rv:+.4f}  t={t(ic_rv):+6.2f}  R2={ic_rv**2*100:5.2f}%")
# combined
X=np.column_stack([today_iv,today_rv]); Xb=np.column_stack([np.ones(n),X])
w=np.linalg.lstsq(Xb,nxt_rv,rcond=None)[0]
pred=Xb@w; ic_c=np.corrcoef(pred,nxt_rv)[0,1]
print(f"    BOTH combined               IC={ic_c:+.4f}  t={t(ic_c):+6.2f}  R2={ic_c**2*100:5.2f}%")
print(f"\n  incremental R2 from my realised-range signal over the market's own IV:")
print(f"    {ic_c**2*100-ic_iv**2*100:+.2f} percentage points")
print()
print("="*100); print("THE VRP TRADE — signal = my forecast vs implied"); print("="*100)
sig=today_rv-today_iv          # positive = realised running hot vs implied
fwd=nxt_rv-today_iv            # what actually happened vs what was priced
q=np.quantile(sig,[.2,.4,.6,.8])
print(f"  {'signal bucket':>28} {'n':>5} {'mean(realised-implied)':>24} {'t':>7}")
for lo,hi,lab in ((-1e9,q[0],'realised << implied (sell vol)'),(q[0],q[1],'q2'),
                  (q[1],q[2],'q3'),(q[2],q[3],'q4'),(q[3],1e9,'realised >> implied (buy vol)')):
    m=(sig>=lo)&(sig<hi)
    if m.sum()<10: continue
    x=fwd[m]
    print(f"  {lab:>28} {m.sum():5d} {x.mean():+23.2f}% {x.mean()/(x.std()/np.sqrt(len(x))):+7.2f}")
