#!/usr/bin/env python3
"""16 CARDINAL ANGLES — shared machinery. Every angle tested on the SAME real bars."""
import sys, json, glob, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
p1=load_1h(); p4=resample_4h(p1)
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)

def arr(panel,a):
    ks=sorted(panel)
    return (np.array(ks),
            np.array([panel[k][a]['open'] for k in ks]),
            np.array([panel[k][a]['high'] for k in ks]),
            np.array([panel[k][a]['low']  for k in ks]),
            np.array([panel[k][a]['close']for k in ks]))
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a
def T(x):
    x=np.asarray(x)
    if len(x)<5 or x.std()==0: return 0.0
    return x.mean()/(x.std()/np.sqrt(len(x)))
def rep(name,x,note=""):
    x=np.asarray(x)
    if len(x)<5:
        print(f"{name:<46} n={len(x):5d}  (too few)"); return None
    print(f"{name:<46} n={len(x):5d}  mean={x.mean()*100:+8.4f}%  t={T(x):+6.2f}  {note}")
    return x
