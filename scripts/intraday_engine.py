"""Agba Metta intraday engine: 1H native + 4H resampled from 1H.
Same rules as daily: all-3-DOWN=SHORT, all-3-UP=LONG, entry=bar open, exit=bar close,
1% hard stop intraday, 20% risk/bar, equal weight /3.
V1 = lev 500, no cap.   V3 = lev 400, basket -2% per-bar loss cap."""
import json,glob,datetime,collections
from pathlib import Path
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

def resample_4h(p1h):
    """Group 1H bars into 4H buckets aligned to 00/04/08/12/16/20 UTC."""
    B=collections.defaultdict(dict)
    for ts in sorted(p1h):
        b=ts-(ts%14400)
        for a in A:
            d=p1h[ts][a]
            if a not in B[b]:
                B[b][a]={'open':d['open'],'high':d['high'],'low':d['low'],'close':d['close'],'n':1}
            else:
                x=B[b][a]
                x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low'])
                x['close']=d['close']; x['n']+=1
    return {t:v for t,v in B.items() if len(v)==3}

def bt(panel,lev=500,risk=0.20,stop=0.01,cap=None,eq0=1e5):
    eq=eq0; peak=eq; bars=[]; nstop=0
    for ts in sorted(panel):
        r=panel[ts]
        dn=all(r[a]['close']<r[a]['open'] for a in A)
        up=all(r[a]['close']>r[a]['open'] for a in A)
        if dn: d=-1
        elif up: d=+1
        else: continue
        pnl=0
        for a in A:
            b=r[a]; e=b['open']
            if d<0:
                s=e*(1+stop)
                ex=s if b['high']>=s else b['close']
                if b['high']>=s: nstop+=1
                ret=(e-ex)/e
            else:
                s=e*(1-stop)
                ex=s if b['low']<=s else b['close']
                if b['low']<=s: nstop+=1
                ret=(ex-e)/e
            pnl+=ret*(eq*risk/3*lev)
        if cap is not None and pnl<-cap*eq: pnl=-cap*eq
        eq+=pnl
        if eq<=0:
            return dict(ret=-100.0,dd=-100.0,n=len(bars)+1,eq=0.0,wr=0.0,stops=nstop,dead=True,
                        S=sum(1 for x in bars if x[1]<0),L=sum(1 for x in bars if x[1]>0))
        peak=max(peak,eq); bars.append((pnl,d,(eq-peak)/peak*100))
    if not bars: return dict(ret=0.0,dd=0.0,n=0,eq=eq0,wr=0.0,stops=0,dead=False,S=0,L=0)
    return dict(ret=(eq/eq0-1)*100,dd=min(x[2] for x in bars),n=len(bars),eq=eq,
                wr=sum(1 for x in bars if x[0]>0)/len(bars)*100,stops=nstop,dead=False,
                S=sum(1 for x in bars if x[1]<0),L=sum(1 for x in bars if x[1]>0))
