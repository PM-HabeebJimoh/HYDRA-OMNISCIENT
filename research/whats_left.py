#!/usr/bin/env python3
"""IS THAT ALL? Honest inventory + what the ONE untested lever would give."""
import math
print("="*94); print("TESTED AND DEAD — direction, from every angle"); print("="*94)
d=[("direct momentum","3 TF","~50%, t -0.88 to +0.49"),
   ("cross-sectional rank","3 assets","t=-1.86"),
   ("lead-lag","6 pairs","gross |t|<1.6, retracted"),
   ("acceleration","3 TF","t=+0.81"),
   ("hour-of-day","24 slots","noise"),
   ("day-of-week","5 slots","noise"),
   ("combinatorial","12 cells","best t=-1.94"),
   ("ML walk-forward","30+ features","48-55% after leak fix"),
   ("rule grid","2,016 configs","best fails noise null"),
   ("causal filters","33 tests","+4.37pp vs +5.10pp noise median")]
for a,b,c in d: print(f"  {a:<22} {b:<14} {c}")
print(f"\n  Ten independent attacks. Direction is settled dead.\n")
print("="*94); print("TESTED AND DEAD — structure"); print("="*94)
s=[("leverage sweep","259,200 configs","MAR flat then falls; 0 above 1000% honestly"),
   ("basket swap","196 baskets","best fails selection null p=0.075"),
   ("V3 cap","-2% basket limit","absorbs $7.0m of real losses = fake"),
   ("V82 port","8 months","+988% but params fitted in-sample"),
   ("36-stream Kelly","73,400 trades","concurrency error; N_eff 7.88 not 36"),
   ("covariance opt","Sigma^-1 mu","8.62 IS -> 0.25 OOS, overfit")]
for a,b,c in s: print(f"  {a:<20} {b:<18} {c}")
print()
print("="*94); print("ALIVE — one edge, passed every gate"); print("="*94)
print("  4H volatility bracket: n=1978, t=+2.76, sign-flip p=0.0020,")
print("  move-size gate correct direction, split-half strengthens.")
print("  WR 49.0% | median monthly +17.9% | maxDD 45.1% at 2.4x")
print()
print("="*94); print("THE ONE GENUINELY UNTESTED LEVER"); print("="*94)
print("  Run THIS verified bracket across uncorrelated instruments.")
print("  Measured cross-asset efficiency (gold/eur/aud + SPX + BTC) = 0.49/instrument")
print("  Sharpe scales sqrt(N_eff). Monthly ROI at fixed DD scales with Sharpe.")
print()
sr_single=2.76/math.sqrt(1978)*math.sqrt(1978/8*12)  # annualised
print(f"  single-stream annual Sharpe = {sr_single:.2f}")
print(f"  {'instruments':>12} {'N_eff':>7} {'port Sharpe':>12} {'median mo ROI @DD~8%':>22}")
for k in (3,10,20,40,65,100):
    neff=0.49*k; sr=sr_single*math.sqrt(neff/ (0.49*3))
    # ROI at fixed 8% DD scales roughly with Sharpe
    roi=17.9*(sr/sr_single)*(8/45.1)*5.6
    print(f"  {k:12d} {neff:7.1f} {sr:12.2f} {roi:21.1f}%")
print()
print("  Even at 100 instruments this reaches ~100-200%/month at 8% DD, not 1000%.")
print("  The honest ceiling for a t=+2.76 edge is a few hundred percent a year,")
print("  not a thousand percent a month.")
