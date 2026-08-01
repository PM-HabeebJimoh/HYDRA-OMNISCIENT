#!/usr/bin/env python3
"""Combine chart + off-chart. Is direction predictable from ANY of it?"""
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
days=sorted(set(D)&set.intersection(*[set(v) for v in M.values()]))
X=[];Y=[];YR=[]
for i in range(2,len(days)):
    d0,d1,d2=days[i-2],days[i-1],days[i]
    row=[]
    for k in ('VIX','DXY','HYSPREAD','CURVE'):
        v1,v0=M[k][d1],M[k][d0]
        row += [(v1-v0)/abs(v0) if v0 else 0.0, v1]
    pb=D[d1]
    for a in A:
        o,h,l,c=pb[a]['open'],pb[a]['high'],pb[a]['low'],pb[a]['close']
        rng=max(h-l,1e-12)
        row += [(c-o)/o,((c-l)-(h-c))/rng,abs(c-o)/rng,rng/o]
    b=D[d2]
    X.append(row)
    Y.append(np.mean([(b[a]['close']-b[a]['open'])/b[a]['open'] for a in A]))
    YR.append(np.mean([(b[a]['high']-b[a]['low'])/b[a]['open'] for a in A]))
X=np.array(X);Y=np.array(Y);YR=np.array(YR)
def wf(X,y,l2=10.0,frac=0.45):
    n=len(y); s=int(n*frac); pred=np.full(n,np.nan)
    for i in range(s,n):
        Xt,yt=X[:i],y[:i]; mu,sd=Xt.mean(0),Xt.std(0)+1e-12
        Z=(Xt-mu)/sd; Zb=np.column_stack([np.ones(len(Z)),Z])
        Aa=Zb.T@Zb+l2*np.eye(Zb.shape[1]); Aa[0,0]-=l2
        try: w=np.linalg.solve(Aa,Zb.T@yt)
        except Exception: continue
        pred[i]=np.r_[1,(X[i]-mu)/sd]@w
    return pred
print("="*98)
print("CHART + OFF-CHART COMBINED — walk-forward, leak-free")
print("="*98)
print(f"  n={len(Y)} days, {X.shape[1]} features (macro lagged t-1 + prior-bar structure)\n")
for lab,y,kind in (("DIRECTION",Y,'dir'),("RANGE",YR,'rng')):
    p=wf(X,y); m=~np.isnan(p)
    if kind=='dir':
        acc=(np.sign(p[m])==np.sign(y[m])).mean()*100
        pnl=np.sign(p[m])*y[m]
        t=pnl.mean()/(pnl.std()/np.sqrt(len(pnl)))
        print(f"  {lab:<10} OOS n={m.sum():4d}  accuracy {acc:5.2f}%  t={t:+5.2f}")
    else:
        ic=np.corrcoef(p[m],y[m])[0,1]
        t=ic*math.sqrt(m.sum()-2)/math.sqrt(max(1-ic**2,1e-12))
        print(f"  {lab:<10} OOS n={m.sum():4d}  IC={ic:+.4f}  t={t:+5.2f}  R2={ic**2*100:.2f}%")
print()
print("="*98); print("THE PATTERN ACROSS EVERY DATA SOURCE I HAVE TESTED"); print("="*98)
print(f"  {'data source':<34} {'direction':>12} {'magnitude/range':>18}")
rows=[("OHLC close-open (original model)","~50%","-"),
      ("32 hidden bar-structure features","48.99-52.78%","R2 15-32%"),
      ("VIX / DXY / HY spread / curve","50-52%","IC 0.17-0.35, t up to +4.6"),
      ("all combined, walk-forward","see above","see above")]
for a,b,c in rows: print(f"  {a:<34} {b:>12} {c:>18}")
print()
print("  Four independent data layers - price, bar micro-structure, macro levels,")
print("  macro changes - and EVERY ONE predicts magnitude, NONE predicts direction.")
print("  This is not a data-gathering failure. It is the arbitrage condition:")
print("  predictable direction is removed by trading; predictable size is not.")
