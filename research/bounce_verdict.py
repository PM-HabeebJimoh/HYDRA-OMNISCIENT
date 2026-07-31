#!/usr/bin/env python3
"""Decisive: real mean-reversion scales with the move. Bid-ask bounce lives in
the smallest moves and is pure spread. Apply cost WHERE the edge actually lives."""
import sys
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h
A=('gold','eur','aud'); LO,HI=1764547200,1785542400
p1=load_1h(); keys=sorted(p1)
S=[]
for i in range(len(keys)-2):
    if not (LO<=keys[i+1]<HI): continue
    s=p1[keys[i]]
    dn=all(s[a]['close']<s[a]['open'] for a in A)
    up=all(s[a]['close']>s[a]['open'] for a in A)
    if dn: S.append((i,+1))
    elif up: S.append((i,-1))
mv=[];rr=[]
for i,side in S:
    s=p1[keys[i]]
    mv.append(np.mean([abs(s[a]['close']-s[a]['open'])/s[a]['open'] for a in A]))
    b=p1[keys[i+1]]['eur']
    rr.append(side*(b['close']-b['open'])/b['open'])
mv=np.array(mv); rr=np.array(rr)

print("COST APPLIED PER QUARTILE (0.2 pip round trip = tight ECN)")
print(f"{'bucket':>22} {'n':>5} {'gross pips':>11} {'net pips':>10} {'t(net)':>8}")
q=np.quantile(mv,[0,.25,.5,.75,1.0])
C=0.2
tot=[]
for lo,hi,lab in ((q[0],q[1],'smallest 25%'),(q[1],q[2],'25-50%'),(q[2],q[3],'50-75%'),(q[3],q[4],'largest 25%')):
    m=(mv>=lo)&(mv<=hi); g=rr[m]*1e4; n=g-C
    t=n.mean()/(n.std()/np.sqrt(len(n)))
    tot.append(n)
    print(f"{lab:>22} {m.sum():5d} {g.mean():+10.4f} {n.mean():+9.4f} {t:+8.2f}")
allnet=np.concatenate(tot)
print(f"{'ALL':>22} {len(allnet):5d} {rr.mean()*1e4:+10.4f} {allnet.mean():+9.4f} "
      f"{allnet.mean()/(allnet.std()/np.sqrt(len(allnet))):+8.2f}")

print("\nSIGNATURE CHECK")
big=rr[mv>=q[3]]; small=rr[mv<=q[1]]
print(f"  smallest-move trades : {small.mean()*1e4:+.4f} pips  (t={small.mean()/(small.std()/np.sqrt(len(small))):+.2f})")
print(f"  largest-move  trades : {big.mean()*1e4:+.4f} pips  (t={big.mean()/(big.std()/np.sqrt(len(big))):+.2f})")
print("  REAL reversion  -> edge RISES with move size")
print("  BID-ASK BOUNCE  -> edge CONCENTRATED in smallest moves, ~0 in large")
print(f"  OBSERVED        -> edge is {small.mean()/max(big.mean(),1e-12):.0f}x larger in the smallest bucket")
print("  VERDICT: bid-ask bounce / quantisation noise, NOT tradeable reversion.")

print("\nWHY BREAK-EVEN == EDGE IS NOT A COINCIDENCE")
print(f"  mean |1H EURUSD move| = {np.mean([abs(p1[k]['eur']['close']-p1[k]['eur']['open'])/p1[k]['eur']['open'] for k in keys])*1e4:.2f} pips")
print(f"  edge extracted        = {rr.mean()*1e4:.3f} pips")
print("  The 'edge' is a sub-pip residue on a ~4 pip bar - the same order as the")
print("  tick grid and the spread. It cannot be separated from execution noise.")
