"""Agba Metta — definitive engine.
Alignment per user spec: candle CLOSES below/above the PREVIOUS candle's close.
Regime filter ON (config): DFII10 > 0.7 = CONTRACTION/SHORT-only,
                           DFII10 < -0.1 = EXPANSION/LONG-only, else no trade.
Sizing: equity*20%/3 per asset, x500. Stop 1% intrabar. Entry open[t], exit close[t]."""
import json
from pathlib import Path
from calendar import monthrange
ROOT=Path(__file__).resolve().parent.parent
A=('gold','eur','aud')
P={}
for f in ("data/market_data_spot2023.json","data/market_data_spot2024.json",
          "data/market_data_spot2025.json","data/market_data_spot.json"):
    P.update(json.loads((ROOT/f).read_text()))
DS=sorted(P)
Y=json.loads((ROOT/"data/market_data_spot2025.json").read_text())

def yield_of(d):
    r=P[d].get('real_yield')
    return r if r is not None else 99.0

def regime(d):
    y=yield_of(d)
    if y>0.7: return -1      # CONTRACTION -> SHORT only
    if y<-0.1: return 1      # EXPANSION -> LONG only
    return 0

def signal(d,mode):
    """mode 'prev'  : close[t] vs close[t-1]   (user spec)
       mode 'open'  : close[t] vs open[t]      (config text)
       mode 'causal': close[t-1] vs close[t-2] (trade next day)"""
    i=DS.index(d)
    if mode=='open':
        dn=all(P[d][a]['close']<P[d][a]['open'] for a in A)
        up=all(P[d][a]['close']>P[d][a]['open'] for a in A)
    elif mode=='prev':
        if i<1: return 0
        p=DS[i-1]
        if not all(a in P[p] for a in A): return 0
        dn=all(P[d][a]['close']<P[p][a]['close'] for a in A)
        up=all(P[d][a]['close']>P[p][a]['close'] for a in A)
    else:
        if i<2: return 0
        p,pp=DS[i-1],DS[i-2]
        if not all(a in P[p] and a in P[pp] for a in A): return 0
        dn=all(P[p][a]['close']<P[pp][a]['close'] for a in A)
        up=all(P[p][a]['close']>P[pp][a]['close'] for a in A)
    return -1 if dn else (1 if up else 0)

def bt(start,end,mode='prev',lev=500,risk=.20,stop=.01,cap=None,eq0=1e5,use_regime=True):
    eq=eq0; peak=eq; rows=[]; ns=0
    for d in [x for x in DS if start<=x<=end]:
        if not all(a in P[d] for a in A): continue
        s=signal(d,mode)
        if s==0: continue
        if use_regime:
            g=regime(d)
            if g==0 or g!=s: continue      # regime must match signal direction
        pnl=0
        for a in A:
            b=P[d][a]; e=b['open']
            if s<0:
                st=e*(1+stop); hit=b['high']>=st; ex=st if hit else b['close']; r=(e-ex)/e
            else:
                st=e*(1-stop); hit=b['low']<=st; ex=st if hit else b['close']; r=(ex-e)/e
            if hit: ns+=1
            pnl+=r*(eq*risk/3*lev)
        if cap is not None and pnl<-cap*eq: pnl=-cap*eq
        eq+=pnl
        if eq<=0:
            return dict(ret=-100.,dd=-100.,n=len(rows)+1,eq=0.,wr=0.,stops=ns,dead=True,S=0,L=0)
        peak=max(peak,eq); rows.append((d,s,pnl,eq,(eq-peak)/peak*100))
    if not rows: return dict(ret=0.,dd=0.,n=0,eq=eq0,wr=0.,stops=0,dead=False,S=0,L=0,rows=[])
    return dict(ret=(eq/eq0-1)*100,dd=min(r[4] for r in rows),n=len(rows),eq=eq,
                wr=sum(1 for r in rows if r[2]>0)/len(rows)*100,stops=ns,dead=False,
                S=sum(1 for r in rows if r[1]<0),L=sum(1 for r in rows if r[1]>0),rows=rows)

def mr(y,m): return f"{y}-{m:02d}-01",f"{y}-{m:02d}-{monthrange(y,m)[1]:02d}"
