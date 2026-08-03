#!/usr/bin/env python3
"""TASK 1 — find 3 percentage points of directional accuracy.
Baseline 4H = 52.61%. Target 56%. Every filter is CAUSAL (uses only the closed
signal candle and earlier). Report accuracy on the alignment signals only."""
import sys, collections, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
import datetime
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
    ks=sorted(P); rows=[]
    for i in range(1,len(ks)-1):
        s=P[ks[i]]; pv=P[ks[i-1]]; nx=P[ks[i+1]]
        up=all(s[a]['close']>s[a]['open'] for a in A)
        dn=all(s[a]['close']<s[a]['open'] for a in A)
        if not (up or dn): continue
        d=1 if up else -1
        fwd=np.mean([(nx[a]['close']-nx[a]['open'])/nx[a]['open'] for a in A])
        body=np.mean([abs(s[a]['close']-s[a]['open'])/s[a]['open'] for a in A])
        rng =np.mean([(s[a]['high']-s[a]['low'])/s[a]['open'] for a in A])
        # close position within the candle range (conviction)
        cp=np.mean([ (s[a]['close']-s[a]['low'])/max(s[a]['high']-s[a]['low'],1e-12) for a in A])
        if d<0: cp=1-cp
        # gap: this candle's open vs prior close
        gap=np.mean([(s[a]['open']-pv[a]['close'])/pv[a]['close'] for a in A])
        # was the PRIOR candle also aligned same way?
        pu=all(pv[a]['close']>pv[a]['open'] for a in A); pdn=all(pv[a]['close']<pv[a]['open'] for a in A)
        cons= 1 if ((d>0 and pu) or (d<0 and pdn)) else 0
        # gold leads?
        gm=(s['gold']['close']-s['gold']['open'])/s['gold']['open']
        rows.append(dict(t=ks[i],d=d,fwd=fwd,body=body,rng=rng,cp=cp,gap=gap,cons=cons,
                         gm=abs(gm),hour=utc(ks[i]).hour,corr=d*fwd>0))
    return rows

def acc(rows,mask=None):
    r=[x for x in rows if (mask is None or mask(x))]
    if len(r)<25: return None,len(r),0
    hit=sum(1 for x in r if x['d']*x['fwd']>0)
    pn=np.array([x['d']*x['fwd'] for x in r])
    return hit/len(r)*100,len(r),pn.mean()/(pn.std()/np.sqrt(len(pn)))

print("="*100)
print("TASK 1 — HUNTING 3 POINTS OF ACCURACY (baseline 4H = 52.61%)")
print("="*100)
for tf in ('DAILY','4H','1H'):
    rows=build(PAN[tf])
    b,n,t=acc(rows)
    print(f"\n--- {tf}  baseline {b:.2f}% (n={n}, t={t:+.2f}) ---")
    body_q=np.quantile([x['body'] for x in rows],[.25,.5,.75])
    cp_q  =np.quantile([x['cp']   for x in rows],[.5,.75])
    tests=[
      ("body in top 25% (strong candles)",   lambda x: x['body']>=body_q[2]),
      ("body in bottom 25% (weak candles)",  lambda x: x['body']<=body_q[0]),
      ("close near extreme (conviction)",    lambda x: x['cp']>=cp_q[1]),
      ("close mid-candle (indecision)",      lambda x: x['cp']<cp_q[0]),
      ("prior candle aligned SAME way",      lambda x: x['cons']==1),
      ("prior candle NOT aligned",           lambda x: x['cons']==0),
      ("gap with the signal",                lambda x: x['d']*x['gap']>0),
      ("gap against the signal",             lambda x: x['d']*x['gap']<0),
      ("gold move > median",                 lambda x: x['gm']>np.median([y['gm'] for y in rows])),
      ("LONG signals only",                  lambda x: x['d']>0),
      ("SHORT signals only",                 lambda x: x['d']<0),
    ]
    out=[]
    for lab,f in tests:
        a_,n_,t_=acc(rows,f)
        if a_ is None: continue
        out.append((a_-b,lab,a_,n_,t_))
    out.sort(reverse=True)
    for dlt,lab,a_,n_,t_ in out:
        flag="  <-- +3pp" if dlt>=3 else ""
        print(f"    {lab:<36} {a_:6.2f}%  ({dlt:+5.2f}pp)  n={n_:4d} t={t_:+5.2f}{flag}")
