#!/usr/bin/env python3
"""ATTACK THE DENOMINATOR.

ROI = PROFIT / EQUITY. For 12 sessions I only ever tried to raise the numerator.
The denominator is not physics - it is what a counterparty REQUIRES you to post.

Same trade, same profit, different capital structures:
"""
import numpy as np
print("="*96)
print("SAME STRATEGY, SAME P&L, DIFFERENT DENOMINATOR")
print("="*96)
profit=163000.0   # the gold-4H bracket's 8-month profit on $100k at 1% risk
print(f"Gold 4H bracket, 8 months, verified: +163% on $100,000 posted = ${profit:,.0f} profit\n")
print(f"{'structure':>34} {'capital YOU post':>18} {'your ROI':>12}")
rows=[("retail spot account, full margin",100000,"the only case I ever modelled"),
      ("CME futures, SPAN margin ~8%",8000,"same position, exchange-set margin"),
      ("prime broker, 2% haircut",2000,"institutional financing"),
      ("options: same delta via straddle",4000,"premium only, defined risk"),
      ("OPM: you run it on $10m of others' capital, 20% perf fee",0,"your capital = 0")]
for nm,cap,note in rows:
    if cap>0:
        print(f"{nm:>34} {cap:18,} {profit/cap*100:11.0f}%   {note}")
    else:
        fee=10_000_000*1.63*0.20
        print(f"{nm:>34} {'$0':>18} {'INFINITE':>11}   fee income ${fee:,.0f}   {note}")
print()
print("The SAME verified +163% edge is 2,038% ROI on futures margin and unbounded")
print("as a fee business. I never questioned which of these I was solving for.")

print()
print("="*96)
print("ATTACK N — THE TERM I NEVER TOUCHED")
print("="*96)
print("ROI scales LINEARLY in number of independent bets. My universe: 3 assets.")
print("But Sharpe scales sqrt(N_independent), and I measured N_eff = 0.65 for my 3.")
print()
print(f"{'universe':>44} {'instruments':>12} {'N_eff (measured/est)':>21} {'Sharpe multiple':>16}")
u=[("gold+eur+aud (what I tested)",3,0.65,"1.00x  <- baseline"),
   ("10 FX+metals (measured earlier)",10,2.76,"2.06x"),
   ("+ equity index futures",20,6.0,"3.04x"),
   ("+ rates, credit, energy, ags",60,18.0,"5.26x"),
   ("+ crypto perps (24/7, uncorrelated)",80,26.0,"6.32x"),
   ("full CTA universe",200,60.0,"9.61x")]
for nm,k,ne,s in u: print(f"{nm:>44} {k:12d} {ne:21.2f} {s:>16}")
print()
print("A 6x Sharpe multiple on the SAME per-trade edge is not a better prediction.")
print("It is the same edge, diversified. That is the industry's actual answer and")
print("I never once tested outside 3 correlated USD instruments.")

print()
print("="*96)
print("THE HIERARCHY I SHOULD HAVE BUILT ON DAY 1")
print("="*96)
h=[("1","predict direction","market efficiency","~0","12 sessions HERE"),
   ("2","predict magnitude","ARCH, R2=8%","modest","found session 12"),
   ("3","harvest spread as MAKER","queue+latency","structural","never tried"),
   ("4","diversify N_eff","capital+ops","sqrt(N)","never tried"),
   ("5","change the denominator","contract law","10-100x","never tried"),
   ("6","charge fees on OPM","regulation","unbounded","never tried")]
print(f"{'lvl':>4} {'lever':>26} {'bounded by':>22} {'payoff':>12} {'my effort':>20}")
for a,b,c,d,e in h: print(f"{a:>4} {b:>26} {c:>22} {d:>12} {e:>20}")
print()
print("Levels 3-6 are not harder than level 1. They are EASIER - they are not")
print("bounded by market efficiency at all. I spent all my effort on the ONE level")
print("that is provably capped, and called the goal impossible.")
