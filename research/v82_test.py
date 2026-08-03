#!/usr/bin/env python3
"""Implement V82.LOWDD's signal + risk model EXACTLY as specified, test on real bars.

Spec logic:
  1H forecast: trend_up = Close>MA20 and MA20>MA50; streak = #bullish bodies in last 3;
               ret_3bar = 3-bar summed pct_change
  BUY  if trend_up   and streak>=2 and ret_3bar>0
  SELL if trend_down and streak<=1 and ret_3bar<0
  entry = close of execution bar, stop = 1*ATR20, target = 2*ATR20,
  MAX_HOLD bars time exit, risk 0.1% of capital, n_units = max(1,int(risk/|S-stop|))

I have real 1H bars for gold/eur/aud (Investing.com, Dec25-Jul26). No 5m.
So: forecast on 4H, execute on 1H (same slow-signal/fast-execution ratio the
spec uses at 1H/5m is 12:1; 4H/1H is 4:1 - closest available). Also run
forecast-1H / execute-1H to isolate the signal itself.
"""
import sys, collections, datetime
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)

def series(panel,a):
    ks=sorted(panel)
    return (np.array(ks),
            np.array([panel[k][a]['open'] for k in ks]),
            np.array([panel[k][a]['high'] for k in ks]),
            np.array([panel[k][a]['low']  for k in ks]),
            np.array([panel[k][a]['close']for k in ks]))

def forecast(o,h,l,c):
    n=len(c)
    body_pos=(c>o).astype(float)
    ma20=np.full(n,np.nan); ma50=np.full(n,np.nan)
    for i in range(19,n): ma20[i]=c[i-19:i+1].mean()
    for i in range(49,n): ma50[i]=c[i-49:i+1].mean()
    ret=np.zeros(n); pct=np.zeros(n); pct[1:]=(c[1:]-c[:-1])/c[:-1]
    ret3=np.full(n,np.nan)
    for i in range(3,n): ret3[i]=pct[i-2:i+1].sum()
    streak=np.full(n,np.nan)
    for i in range(2,n): streak[i]=body_pos[i-2:i+1].sum()
    tu=(c>ma20)&(ma20>ma50); td=(c<ma20)&(ma20<ma50)
    return tu,td,streak,ret3

def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n)
    tr[0]=h[0]-l[0]
    for i in range(1,n):
        tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a

def run(fpanel,xpanel,max_hold,risk=0.001,cap0=10000.0,smult=1.0,tmult=2.0,min_streak=2):
    cap=cap0; peak=cap; mdd=0.0; trades=[]
    fk=np.array(sorted(fpanel))
    for a in A:
        pass
    # per-asset execution, shared capital, chronological merge
    events=[]
    for a in A:
        xk,xo,xh,xl,xc=series(xpanel,a)
        fk2,fo,fh,fl,fc=series(fpanel,a)
        tu,td,st,r3=forecast(fo,fh,fl,fc)
        av=atr(xh,xl,xc,20)
        import bisect
        for i in range(60,len(xc)-max_hold):
            j=bisect.bisect_right(list(fk2),xk[i])-1
            if j<60: continue
            if np.isnan(st[j]) or np.isnan(r3[j]) or np.isnan(av[i]): continue
            d=None
            if tu[j] and st[j]>=min_streak and r3[j]>0: d='BUY'
            elif td[j] and st[j]<=(3-min_streak) and r3[j]<0: d='SELL'
            if d is None: continue
            events.append((xk[i],a,i,d,xc[i],av[i],xk,xo,xh,xl,xc))
    events.sort(key=lambda e:e[0])
    for ts,a,i,d,S,av_,xk,xo,xh,xl,xc in events:
        stop = S-smult*av_ if d=='BUY' else S+smult*av_
        tgt  = S+tmult*av_ if d=='BUY' else S-tmult*av_
        rd=cap*risk; dist=abs(S-stop)
        if dist<=0: continue
        nu=max(1,int(rd/dist))
        ex=None; why='time'
        for j in range(i+1,min(i+max_hold,len(xc))):
            if d=='BUY':
                if xl[j]<=stop: ex=stop; why='stop'; break
                if xh[j]>=tgt:  ex=tgt;  why='target'; break
            else:
                if xh[j]>=stop: ex=stop; why='stop'; break
                if xl[j]<=tgt:  ex=tgt;  why='target'; break
        if ex is None:
            k=min(i+max_hold,len(xc)-1); ex=xc[k]
        pnl=(ex-S)*nu if d=='BUY' else (S-ex)*nu
        cap+=pnl; peak=max(peak,cap); mdd=max(mdd,(peak-cap)/peak)
        trades.append((pnl,why,pnl/rd if rd>0 else 0))
        if cap<=0: break
    if not trades: return None
    p=np.array([t[0] for t in trades]); R=np.array([t[2] for t in trades])
    w=collections.Counter(t[1] for t in trades)
    return dict(n=len(trades),cap=cap,ret=(cap/cap0-1)*100,mdd=mdd*100,
                wr=(p>0).mean()*100,meanR=R.mean(),exits=w)

print("="*84)
print("V82.LOWDD LOGIC ON REAL DATA (gold/eur/aud, Investing.com, Dec25-Jul26)")
print("="*84)
for lab,fp,xp,mh in (("forecast 4H / execute 1H (12:1-style)",p4,p1,12),
                     ("forecast 1H / execute 1H (signal only)",p1,p1,12)):
    r=run(fp,xp,mh)
    if not r: print(f"{lab}: no trades"); continue
    print(f"\n{lab}")
    print(f"  trades {r['n']:,}   win rate {r['wr']:.2f}%   mean {r['meanR']:+.4f}R")
    print(f"  final ${r['cap']:,.2f} from $10,000   ROI {r['ret']:+.2f}%   maxDD {r['mdd']:.2f}%")
    tot=sum(r['exits'].values())
    print(f"  exits: "+"  ".join(f"{k}={v} ({v/tot*100:.1f}%)" for k,v in r['exits'].most_common()))
