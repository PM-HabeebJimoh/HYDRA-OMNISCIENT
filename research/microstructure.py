#!/usr/bin/env python3
"""Is the EURUSD 1H 'edge' real mean-reversion, or a microstructure artifact?

The trade is: bar i closes (all 3 down) -> BUY at bar i+1 OPEN -> sell at bar i+1 CLOSE.
That return decomposes into nothing but the bar i+1 body. But the SIGNAL comes from
bar i's close. In a continuous market open[i+1] should equal close[i].
If the provider's open[i+1] != close[i], the 'edge' may live in a synthetic seam.

Tests:
  A. how far is open[i+1] from close[i]?
  B. DELAY test - enter at bar i+2 open instead. Real reversion partially persists;
     a one-bar bounce artifact vanishes.
  C. does the edge survive if we measure close[i]->close[i+1] instead of open->close?
  D. is the edge concentrated after SMALL prior moves (noise) or LARGE ones (real)?
"""
import sys, datetime
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h
A=('gold','eur','aud'); LO,HI=1764547200,1785542400
p1=load_1h(); keys=sorted(p1)

# ---------- A. seam between bars ----------
gap=[]; body=[]
for i in range(len(keys)-1):
    c0=p1[keys[i]]['eur']['close']; o1=p1[keys[i+1]]['eur']['open']
    gap.append((o1-c0)/c0)
gap=np.array(gap)
print("A. SEAM: open[i+1] vs close[i] for EURUSD 1H")
print(f"   bars compared      : {len(gap)}")
print(f"   exactly equal      : {(gap==0).sum()} ({(gap==0).mean()*100:.1f}%)")
print(f"   mean |gap|         : {np.abs(gap).mean()*1e4:.4f} pips")
print(f"   max  |gap|         : {np.abs(gap).max()*1e4:.2f} pips")
print("   -> if most opens equal prior closes, the feed is continuous and the")
print("      trade is a clean bar-body bet.\n")

# ---------- build signal ----------
def sig_idx():
    out=[]
    for i in range(len(keys)-2):
        if not (LO<=keys[i+1]<HI): continue
        s=p1[keys[i]]
        dn=all(s[a]['close']<s[a]['open'] for a in A)
        up=all(s[a]['close']>s[a]['open'] for a in A)
        if dn: out.append((i,+1))     # FADE a down-alignment = BUY
        elif up: out.append((i,-1))
    return out
S=sig_idx()
print(f"signals: {len(S)}")

def stat(r,lab):
    r=np.array(r)
    t=r.mean()/(r.std()/np.sqrt(len(r))) if len(r)>2 else 0
    print(f"   {lab:<44} n={len(r):5d}  mean={r.mean()*1e4:+7.4f} pips  t={t:+6.2f}")
    return r

print("\nB. DELAY TEST (does the edge persist beyond one bar?)")
for d in (1,2,3):
    r=[]
    for i,side in S:
        j=i+d
        if j>=len(keys): continue
        b=p1[keys[j]]['eur']
        r.append(side*(b['close']-b['open'])/b['open'])
    stat(r,f"enter bar i+{d} open -> that bar close")

print("\nC. WHERE DOES THE RETURN LIVE?")
r_body=[];r_c2c=[];r_seam=[]
for i,side in S:
    if i+1>=len(keys): continue
    c0=p1[keys[i]]['eur']['close']; b=p1[keys[i+1]]['eur']
    r_body.append(side*(b['close']-b['open'])/b['open'])       # what we trade
    r_c2c .append(side*(b['close']-c0)/c0)                      # close->close
    r_seam.append(side*(b['open']-c0)/c0)                       # the seam itself
stat(r_body,"bar body  open[i+1]->close[i+1]  (the trade)")
stat(r_c2c ,"close[i]->close[i+1]")
stat(r_seam,"seam only close[i]->open[i+1]")

print("\nD. EDGE vs SIZE OF THE TRIGGERING MOVE")
mv=[];rr=[]
for i,side in S:
    if i+1>=len(keys): continue
    s=p1[keys[i]]
    m=np.mean([abs(s[a]['close']-s[a]['open'])/s[a]['open'] for a in A])
    b=p1[keys[i+1]]['eur']
    mv.append(m); rr.append(side*(b['close']-b['open'])/b['open'])
mv=np.array(mv); rr=np.array(rr)
q=np.quantile(mv,[0,.25,.5,.75,1.0])
for lo,hi,lab in ((q[0],q[1],'smallest 25% moves'),(q[1],q[2],'25-50%'),
                  (q[2],q[3],'50-75%'),(q[3],q[4],'largest 25% moves')):
    m=(mv>=lo)&(mv<=hi)
    stat(rr[m],lab)
print("   -> a real reversion edge grows with the size of the move.")
print("      A noise/bounce artifact is flat or concentrated in the SMALLEST moves.")
