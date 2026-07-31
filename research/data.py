"""Load 100% real Investing.com bars into numpy arrays. No synthetic fill, no interpolation."""
import json,glob,collections,datetime
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'data/raw/intraday'
A=('gold','eur','aud'); SYM={'XAUUSD':'gold','EURUSD':'eur','AUDUSD':'aud'}

def load_1h():
    P=collections.defaultdict(dict)
    for f in sorted(glob.glob(str(RAW/'*.json'))):
        r=json.load(open(f)); a=SYM[r['symbol']]
        for i,ts in enumerate(r['t']):
            P[ts][a]={'open':r['o'][i],'high':r['h'][i],'low':r['l'][i],'close':r['c'][i]}
    return {t:v for t,v in P.items() if len(v)==3}

def resample(p1h,secs):
    B=collections.defaultdict(dict)
    for ts in sorted(p1h):
        b=ts-(ts%secs)
        for a in A:
            d=p1h[ts][a]
            if a not in B[b]: B[b][a]=dict(d); B[b][a]['n']=1
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low'])
                x['close']=d['close']; x['n']+=1
    return {t:v for t,v in B.items() if len(v)==3}

def to_arrays(panel):
    ts=np.array(sorted(panel),dtype=np.int64)
    O=np.empty((len(ts),3));H=np.empty_like(O);L=np.empty_like(O);C=np.empty_like(O)
    for i,t in enumerate(ts):
        for j,a in enumerate(A):
            b=panel[t][a]; O[i,j]=b['open'];H[i,j]=b['high'];L[i,j]=b['low'];C[i,j]=b['close']
    return dict(ts=ts,O=O,H=H,L=L,C=C,A=A)

def daily_from_1h(p1h):
    return resample(p1h,86400)

def utc(t): return datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)

def panels():
    p1=load_1h()
    return dict(H1=to_arrays(p1),H4=to_arrays(resample(p1,14400)),D1=to_arrays(daily_from_1h(p1)))
