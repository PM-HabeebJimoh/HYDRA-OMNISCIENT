"""Agba Metta — LIVE-CORRECT model (user spec, next-candle entry).
1. Wait for candle close.
2. Direction per asset: close>open=UP, close<open=DOWN.
3. all UP  -> LONG ; all DOWN -> SHORT ; mixed -> skip.
4. ENTER on NEXT candle open.
5. 20% equity split /3, 500x.
6. LONG stop=entry*0.99, SHORT stop=entry*1.01 (from ACTUAL entry price).
7. Exit at NEXT candle close unless stop hit first.
"""
import json
from pathlib import Path
from calendar import monthrange
ROOT=Path(__file__).resolve().parent.parent
A=('gold','eur','aud')

def load_daily():
    P={}
    for f in ("data/market_data_spot2023.json","data/market_data_spot2024.json",
              "data/market_data_spot2025.json","data/market_data_spot.json"):
        P.update(json.loads((ROOT/f).read_text()))
    return P

def direction(bar):
    if bar['close']>bar['open']: return 'UP'
    if bar['close']<bar['open']: return 'DOWN'
    return 'FLAT'

def bt_live(P,keys,lev=500,risk=.20,stop=.01,cap=None,eq0=1e5,
            use_regime=False,start=None,end=None):
    """keys = ordered list of candle keys. Signal on keys[i], ENTRY on keys[i+1]."""
    eq=eq0; peak=eq; rows=[]; ns=0
    for i in range(len(keys)-1):
        sk, ek = keys[i], keys[i+1]          # signal candle, entry candle
        s, e_ = P[sk], P[ek]
        if not all(a in s for a in A) or not all(a in e_ for a in A): continue
        dirs=[direction(s[a]) for a in A]
        if all(d=='DOWN' for d in dirs):  side=-1
        elif all(d=='UP' for d in dirs):  side=1
        else: continue
        if use_regime:
            y=s.get('real_yield',99.)
            g = -1 if y>0.7 else (1 if y<-0.1 else 0)
            if g==0 or g!=side: continue
        # date filter applies to the ENTRY candle
        if start and str(ek)<start: continue
        if end and str(ek)>end: continue
        per=eq*risk/3; pnl=0; legs=[]
        for a in A:
            b=e_[a]; entry=b['open']
            if side<0:
                st=entry*(1+stop); hit=b['high']>=st; ex=st if hit else b['close']
                r=(entry-ex)/entry
            else:
                st=entry*(1-stop); hit=b['low']<=st; ex=st if hit else b['close']
                r=(ex-entry)/entry
            if hit: ns+=1
            p=r*per*lev; pnl+=p
            legs.append((a,entry,st,ex,r*100,'STOP' if hit else 'CLOSE',p))
        if cap is not None and pnl<-cap*eq: pnl=-cap*eq
        eq+=pnl
        if eq<=0:
            rows.append((sk,ek,side,pnl,0.0,-100.,legs))
            return dict(ret=-100.,dd=-100.,n=len(rows),eq=0.,wr=0.,stops=ns,dead=True,
                        S=sum(1 for r in rows if r[2]<0),L=sum(1 for r in rows if r[2]>0),rows=rows)
        peak=max(peak,eq); rows.append((sk,ek,side,pnl,eq,(eq-peak)/peak*100,legs))
    if not rows:
        return dict(ret=0.,dd=0.,n=0,eq=eq0,wr=0.,stops=0,dead=False,S=0,L=0,rows=[])
    return dict(ret=(eq/eq0-1)*100,dd=min(r[5] for r in rows),n=len(rows),eq=eq,
                wr=sum(1 for r in rows if r[3]>0)/len(rows)*100,stops=ns,dead=False,
                S=sum(1 for r in rows if r[2]<0),L=sum(1 for r in rows if r[2]>0),rows=rows)

def mr(y,m): return f"{y}-{m:02d}-01",f"{y}-{m:02d}-{monthrange(y,m)[1]:02d}"
