#!/usr/bin/env python3
"""COMBINE ALL HIDDEN LAYERS — walk-forward, leak-free.
Individually weak features can be jointly predictive. Test that properly.
Also test the PREDICTIVE (anticipatory) target: next-bar RANGE, not direction."""
import sys, collections, datetime, math
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
def build(P):
    ks=sorted(P); X=[]; ydir=[]; yrng=[]; T=[]
    hist={a:[] for a in A}
    for i in range(22,len(ks)-1):
        b=P[ks[i]]; pv=P[ks[i-1]]; nx=P[ks[i+1]]
        row=[]
        for a in A:
            o,h,l,c=b[a]['open'],b[a]['high'],b[a]['low'],b[a]['close']
            rng=max(h-l,1e-12)
            row += [(c-o)/o,(h-max(o,c))/o,(min(o,c)-l)/o,
                    ((c-l)-(h-c))/rng, abs(c-o)/rng,
                    (o-pv[a]['close'])/pv[a]['close'],
                    ((h-max(o,c))-(min(o,c)-l))/rng, rng/o]
        # trailing realised vol (causal)
        for a in A:
            past=[ (P[ks[j]][a]['high']-P[ks[j]][a]['low'])/P[ks[j]][a]['open'] for j in range(i-20,i)]
            row.append(np.mean(past)); row.append(np.std(past))
        clv=[((b[a]['close']-b[a]['low'])-(b[a]['high']-b[a]['close']))/max(b[a]['high']-b[a]['low'],1e-12) for a in A]
        row += [np.mean(clv),np.std(clv)]
        X.append(row)
        ydir.append(np.mean([(nx[a]['close']-nx[a]['open'])/nx[a]['open'] for a in A]))
        yrng.append(np.mean([(nx[a]['high']-nx[a]['low'])/nx[a]['open'] for a in A]))
        T.append(ks[i])
    return np.array(X),np.array(ydir),np.array(yrng),np.array(T)

def wf_ridge(X,y,l2=10.0,frac=0.4):
    n=len(y); s=int(n*frac); pred=np.full(n,np.nan)
    for i in range(s,n):
        Xt,yt=X[:i],y[:i]
        mu,sd=Xt.mean(0),Xt.std(0)+1e-12
        Z=(Xt-mu)/sd
        Zb=np.column_stack([np.ones(len(Z)),Z])
        Aa=Zb.T@Zb+l2*np.eye(Zb.shape[1]); Aa[0,0]-=l2
        try: w=np.linalg.solve(Aa,Zb.T@yt)
        except Exception: continue
        z=(X[i]-mu)/sd
        pred[i]=np.r_[1,z]@w
    return pred

print("="*100)
print("COMBINE ALL LAYERS — walk-forward ridge, leak-free")
print("="*100)
for tf in ('DAILY','4H','1H'):
    X,yd,yr,T=build(PAN[tf])
    print(f"\n--- {tf}  n={len(yd)}  features={X.shape[1]} ---")
    # TARGET 1: DIRECTION
    p=wf_ridge(X,yd)
    m=~np.isnan(p)
    pnl=np.sign(p[m])*yd[m]
    acc=(np.sign(p[m])==np.sign(yd[m])).mean()*100
    t=pnl.mean()/(pnl.std()/np.sqrt(len(pnl)))
    print(f"  TARGET=DIRECTION : OOS n={m.sum():4d}  acc={acc:5.2f}%  t={t:+5.2f}")
    # TARGET 2: RANGE (anticipatory)
    p2=wf_ridge(X,yr)
    m2=~np.isnan(p2)
    ic=np.corrcoef(p2[m2],yr[m2])[0,1]
    tt=ic*math.sqrt(m2.sum()-2)/math.sqrt(max(1-ic**2,1e-12))
    print(f"  TARGET=RANGE     : OOS n={m2.sum():4d}  IC={ic:+.4f}  t={tt:+5.2f}  R2={ic**2*100:.2f}%")
