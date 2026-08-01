#!/usr/bin/env python3
"""FIRST PRINCIPLES: what IS a monthly ROI, algebraically?

    ROI = (edge_per_trade x N_trades x notional_per_trade) / EQUITY

Four independent multiplicands. For 12 sessions I have attacked exactly ONE:
edge_per_trade. I proved it is ~0 and then declared the goal impossible.

That is a category error. The other three are NOT bounded by market efficiency.
They are bounded by ENGINEERING, CONTRACT STRUCTURE and WHO YOU ARE IN THE TRADE.

Enumerate every term. Find which are physics and which are convention.
"""
import sys
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)

print("="*94)
print("THE FOUR TERMS OF ROI — which did I ever question?")
print("="*94)
rows=[("edge per trade","market efficiency","PHYSICS - bounded. I proved ~0.","ATTACKED 12 sessions"),
      ("N trades","bars available x instruments","ENGINEERING - not bounded by efficiency","never questioned"),
      ("notional / trade","broker margin rules","CONTRACT - not physics","only as 'leverage'"),
      ("EQUITY (denominator)","what you must POST","CONTRACT - not physics","NEVER QUESTIONED")]
print(f"{'term':>18} {'set by':>28} {'nature':>42}")
for a,b,c,d in rows: print(f"{a:>18} {b:>28} {c:>42}\n{'':>18} {'-> my treatment: '+d}")

print()
print("="*94)
print("ANGLE — WHO PAYS THE SPREAD? (the sign-flip I never considered)")
print("="*94)
print("My EURUSD 1H result died because the 0.417 pip edge equalled the spread.")
print("I called it 'bid-ask bounce' and threw it away.")
print()
print("But bid-ask bounce is not noise. It is REVENUE - to the party who QUOTES.")
print("I have spent 12 sessions as a price TAKER, paying that number every trade.")
print("The identical number, with the sign flipped, is the market maker's P&L.")
print()
ks=np.array(sorted(p1))
for a in A:
    o=np.array([p1[k][a]['open'] for k in ks]); c=np.array([p1[k][a]['close'] for k in ks])
    h=np.array([p1[k][a]['high'] for k in ks]); l=np.array([p1[k][a]['low'] for k in ks])
    rng=(h-l)/o
    print(f"  {a:>5}: mean 1H range {rng.mean()*1e4:7.2f} bp   bars={len(ks)}")
    print(f"         a maker quoting both sides captures ~half-spread per round trip.")
print()
print("Order of magnitude, EURUSD, 1 lot ($100k) quoting 0.2 pip half-spread:")
print("   revenue per filled round trip = 0.2 pip x $100k = $2.00")
print("   fills needed for $1,000/day    = 500 round trips")
print("   EURUSD trades ~$1.1 TRILLION/day. 500 round trips is invisible.")
print("   THE CONSTRAINT IS NOT MARKET EFFICIENCY. IT IS QUEUE POSITION + LATENCY.")
print("   That is an ENGINEERING problem, not a prediction problem.")

print()
print("="*94)
print("ANGLE — ADVERSE SELECTION: why this is not free money")
print("="*94)
print("A maker gets filled when someone wants the other side. On average the taker")
print("is INFORMED. Measure it: after a bar breaks its own range, what happens next?")
for a in A:
    o=np.array([p1[k][a]['open'] for k in ks]); c=np.array([p1[k][a]['close'] for k in ks])
    r=(c-o)/o
    big=np.abs(r)>np.quantile(np.abs(r),0.9)
    cont=np.sign(r[:-1])[big[:-1]]*r[1:][big[:-1]]
    print(f"  {a:>5}: after the largest 10% of bars, next-bar continuation = "
          f"{cont.mean()*1e4:+7.3f} bp (t={cont.mean()/(cont.std()/np.sqrt(len(cont))):+.2f})")
print("  -> if strongly positive, makers get run over on big bars. That is the real cost.")
