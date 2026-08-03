"""
THE KILL TEST for R2.

Audit A-G all passed: WR 83.7%, t=+5.8..+9.8, 20/21 months positive,
sign-flip p=0.0000, survives pessimistic stops, works in BOTH vol regimes,
+48.94%/mo at 22.96% DD on 4x.

But test C is a red flag I must not ignore:

    stop 1.5 -> t=+3.76 | 2.0 -> +5.76 | 3.0 -> +8.26 | 5.0 -> +10.43 | none -> +11.29

The edge is MONOTONICALLY BEST WITH NO STOP AT ALL. A strategy that improves
as you remove risk control is usually not an edge -- it is an unbounded short
tail that this 8-month window never sampled. That is exactly the shape of
"picking up pennies in front of a steamroller".

Three decisive tests:

 1. INTRABAR PATH. My fade() reads only the 4H OHLC. If a bar goes to the stop
    and comes back, OHLC still shows the touch, but if it goes THROUGH and
    keeps going I book -stop. Real fills gap past stops. Rebuild the exact
    same trade on 1H sub-bars where I can see the path, and compare.

 2. THE STEAMROLLER. What is the worst possible bar in a longer history, and
    what would it do at 4x? Use the 348 weekly + all available data to size
    the true tail rather than the 8-month sample.

 3. IS IT MEAN REVERSION OR IS IT THE SPREAD? Test the fade with NO band at
    all (pure "close reverts to open") to see what is actually being paid.
"""
import json, sys, glob, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import tstat, signflip_null

def say(*a): print(*a, flush=True)

p1h = load_1h(); p4 = resample_4h(p1h)
b1 = sorted(p1h); b4 = sorted(p4); N = len(b4)
SPREAD = {'gold':0.00012,'eur':0.000045,'aud':0.000075}

def series(a):
    out,pc=[],None
    for t in b4:
        x=p4[t][a]
        out.append((t,x['open'],x['high'],x['low'],x['close'],pc if pc else x['open']))
        pc=x['close']
    return out
S={a:series(a) for a in A}

# 1H bars grouped into their 4H bucket, in order
SUB=collections.defaultdict(list)
for t in b1:
    SUB[t-(t%14400)].append(t)

def fade_ohlc(a,i,w_mult=1.0,stop_mult=2.0):
    q=S[a]
    hist=[(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i+1)]
    w=float(np.mean(hist))*w_mult; stop=stop_mult*w
    _,o,h,l,c,_=q[i+1]; hs=SPREAD[a]
    up,dn=o*(1+w),o*(1-w); su,sd=o*(1+stop),o*(1-stop)
    hu,hd=h>=up,l<=dn; su_,sd_=h>=su,l<=sd
    if su_ and sd_: return -2*stop-2*hs
    if su_ or sd_:  return -stop-hs
    if hu and hd:   return 2*w-2*hs
    if hu:          return (up-c)/o-hs
    if hd:          return (c-dn)/o-hs
    return abs(c-o)/o-hs

def fade_path(a,i,w_mult=1.0,stop_mult=2.0):
    """Same trade, but walk the 1H sub-bars in ORDER so entries/stops
    happen in the true sequence. Positions: short above band, long below."""
    q=S[a]
    hist=[(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i+1)]
    w=float(np.mean(hist))*w_mult; stop=stop_mult*w
    tb=q[i+1][0]
    subs=SUB.get(tb,[])
    if len(subs)<2: return None
    o=p1h[subs[0]][a]['open']; hs=SPREAD[a]
    up,dn=o*(1+w),o*(1-w); su,sd=o*(1+stop),o*(1-stop)
    pos=0; entry=0.0; pnl=0.0
    for t in subs:
        b=p1h[t][a]; hi,lo,cl=b['high'],b['low'],b['close']
        # stop check first (worst-case ordering for us)
        if pos<0 and hi>=su:
            pnl+=(entry-su)/o-hs; pos=0; return pnl
        if pos>0 and lo<=sd:
            pnl+=(sd-entry)/o-hs; pos=0; return pnl
        if pos==0:
            if hi>=up: pos=-1; entry=up
            elif lo<=dn: pos=+1; entry=dn
    if pos<0:  pnl+=(entry-p1h[subs[-1]][a]['close'])/o-hs
    elif pos>0:pnl+=(p1h[subs[-1]][a]['close']-entry)/o-hs
    else:      pnl+=abs(p1h[subs[-1]][a]['close']-o)/o-hs
    return pnl

say("="*78)
say("1. OHLC ASSUMPTION vs TRUE 1H INTRABAR PATH")
say("="*78)
say("Same trade, same band, same stop. Only difference: path visibility.")
for a in A:
    oh,pa=[],[]
    for i in range(210,N-1):
        v1=fade_ohlc(a,i); v2=fade_path(a,i)
        if v2 is None: continue
        oh.append(v1); pa.append(v2)
    m1,t1,n1=tstat(oh); m2,t2,n2=tstat(pa)
    say(f"  {a:5s} OHLC  mean {m1*100:+.4f}%  t={t1:+6.2f}  "
        f"WR {np.mean([x>0 for x in oh])*100:.1f}%  n={n1}")
    say(f"        PATH  mean {m2*100:+.4f}%  t={t2:+6.2f}  "
        f"WR {np.mean([x>0 for x in pa])*100:.1f}%  n={n2}")
    say(f"        -> path/OHLC edge ratio {m2/m1 if m1 else float('nan'):.3f}")

say(); say("="*78)
say("2. THE STEAMROLLER -- how bad is the true tail?")
say("="*78)
say("Largest adverse 4H excursions in the sample, and what an unstopped")
say("fade would have lost on them at various leverage.")
for a in A:
    q=S[a]
    moves=[]
    for i in range(21,N):
        hist=[(q[j][2]-q[j][3])/q[j][1] for j in range(i-21,i)]
        w=float(np.mean(hist))
        _,o,h,l,c,_=q[i]
        exc=max((h-o)/o,(o-l)/o)/w if w>0 else 0
        moves.append(exc)
    moves=np.array(moves)
    say(f"  {a:5s} excursion / band :  median {np.median(moves):.2f}x   "
        f"95th {np.quantile(moves,.95):.2f}x   99th {np.quantile(moves,.99):.2f}x   "
        f"MAX {moves.max():.2f}x")
    worst=moves.max()
    say(f"        an unstopped fade on that bar loses {worst*100*0.0:.0f}"
        f"~{(worst-1)*np.mean([ (q[j][2]-q[j][3])/q[j][1] for j in range(21,N)])*100:.2f}% "
        f"of notional; at 4x that is "
        f"{(worst-1)*np.mean([(q[j][2]-q[j][3])/q[j][1] for j in range(21,N)])*400:.1f}% of equity")

say(); say("="*78)
say("3. WHAT IS ACTUALLY BEING PAID? decompose the fade")
say("="*78)
say("If the band never trades, I book |c-o| as profit -- that is NOT a trade,")
say("it is an accounting artifact. How often does that branch fire?")
for a in A:
    q=S[a]; cnt=collections.Counter(); contrib=collections.defaultdict(float)
    for i in range(210,N-1):
        hist=[(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i+1)]
        w=float(np.mean(hist)); stop=2.0*w
        _,o,h,l,c,_=q[i+1]; hs=SPREAD[a]
        up,dn=o*(1+w),o*(1-w); su,sd=o*(1+stop),o*(1-stop)
        hu,hd=h>=up,l<=dn; su_,sd_=h>=su,l<=sd
        if su_ and sd_: k,v='both stops',-2*stop-2*hs
        elif su_ or sd_:k,v='one stop',-stop-hs
        elif hu and hd: k,v='faded both',2*w-2*hs
        elif hu:        k,v='faded up',(up-c)/o-hs
        elif hd:        k,v='faded down',(c-dn)/o-hs
        else:           k,v='NEVER TRADED',abs(c-o)/o-hs
        cnt[k]+=1; contrib[k]+=v
    tot=sum(contrib.values())
    say(f"  {a.upper()}  total {tot*100:+.2f}%")
    for k in sorted(contrib,key=lambda x:-abs(contrib[x])):
        say(f"      {k:14s} n={cnt[k]:4d}  contributes {contrib[k]*100:+8.2f}%  "
            f"({contrib[k]/tot*100 if tot else 0:+6.1f}% of total)")
