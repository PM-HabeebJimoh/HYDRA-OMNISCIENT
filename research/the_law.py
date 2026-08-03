#!/usr/bin/env python3
"""SIX data layers, ~60 tests. Tabulate direction vs magnitude across ALL of them.
Then test the ONE question that matters: is the direction result consistent with
pure chance, and is the magnitude result consistent with real information?"""
import numpy as np, math
print("="*100)
print("EVERY DATA LAYER TESTED IN THIS PROJECT — direction vs magnitude")
print("="*100)
rows=[
 ("1. price close-open (the model)","~50%","t +0.21/+0.49/-0.88","—","—"),
 ("2. bar microstructure, 32 feats","48.99-52.78%","t ~0","R2 15-32%","t +32.32"),
 ("3. macro levels VIX/DXY/HY/curve","50-52%","best |t| 1.83","IC .17-.35","t +4.61"),
 ("4. macro changes (d/dt)","~50%","|t| < 1.9","IC .05-.17","t +2.10"),
 ("5. implied vol GVZ (options mkt)","—","—","R2 32%","t +8.65"),
 ("6. cross-market RATIOS","49-51%","|t| < 0.9","IC .33-.40","t +5.50"),
 ("7. conditional on 6 macro states","43-58%","ALL |t| < 0.9","—","—"),
]
print(f"  {'layer':<36} {'DIRECTION':>16} {'t':>18} {'MAGNITUDE':>12} {'t':>10}")
for a,b,c,d,e in rows: print(f"  {a:<36} {b:>16} {c:>18} {d:>12} {e:>10}")
print()
print("="*100); print("IS THE DIRECTION RESULT JUST CHANCE?"); print("="*100)
ts=[0.21,0.49,-0.88,0.08,-1.74,0.73,0.77,0.56,1.73,1.83,-0.30,-0.12,0.38,0.54,
    -0.88,-0.62,-0.44,0.06,-0.02,-0.06,0.42,0.56,-0.00,0.63,0.60,-0.89,0.63,0.02,-0.37,-0.72]
ts=np.array(ts); n=len(ts)
print(f"  {n} independent direction t-stats collected across all layers")
print(f"  mean t = {ts.mean():+.3f}   sd = {ts.std():.3f}   (chance: mean 0, sd 1)")
print(f"  |t|>1.96 count = {(np.abs(ts)>1.96).sum()} of {n}   expected by chance = {0.05*n:.1f}")
print(f"  max |t| = {np.abs(ts).max():.2f}   expected max from {n} draws = {math.sqrt(2*math.log(n)):.2f}")
print("  -> direction results are INDISTINGUISHABLE from random noise.")
print()
print("="*100); print("IS THE MAGNITUDE RESULT REAL?"); print("="*100)
mt=[32.32,4.61,2.10,8.65,5.50,4.45,4.56,3.31,2.82,3.49,11.43,2.24]
mt=np.array(mt)
print(f"  {len(mt)} magnitude t-stats: min {mt.min():.2f}, median {np.median(mt):.2f}, max {mt.max():.2f}")
print(f"  |t|>1.96 count = {(np.abs(mt)>1.96).sum()} of {len(mt)} = {(np.abs(mt)>1.96).mean()*100:.0f}%")
print(f"  expected by chance = {0.05*len(mt):.1f}")
print("  -> magnitude is real information, found INDEPENDENTLY in 6 separate data sources.")
print()
print("="*100); print("THE LAW, STATED PRECISELY"); print("="*100)
print("  Across 6 independent data layers and ~60 tests:")
print("    DIRECTION : 0 of 30 tests significant. Mean t = %.2f. Pure noise." % ts.mean())
print("    MAGNITUDE : 12 of 12 tests significant. Median t = %.1f." % np.median(mt))
print()
print("  This is the arbitrage condition, measured six ways:")
print("    Direction is the ONE thing whose prediction is self-destroying.")
print("    If it were predictable, trading it removes the prediction.")
print("    Magnitude prediction is NOT self-destroying - knowing something will")
print("    move does not tell you which way, so the information survives.")
print()
print("  >700%/month at low DD requires DIRECTION. That is the one quantity")
print("  that six independent data sources agree is not there.")
