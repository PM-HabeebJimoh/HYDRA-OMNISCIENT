"""What does 700%/mo with DD<5% actually REQUIRE? Pure arithmetic, no model."""
import numpy as np, math
from research.data import panels,utc
P=panels()

print("=== 1. THE LEVERAGE ILLUSION ===")
print("Loss on a trade = (notional/equity) * adverse_move.  Leverage only sets notional/equity.")
print("Old model: risk 20% eq /3 assets * 500x = notional 33.3x equity PER ASSET.")
print("  a 1.0% stop  -> -33.3% equity on ONE leg.  3 legs -> -100%.")
print("  So DD<5% is ARITHMETICALLY IMPOSSIBLE with 1% stop at that size. Not a tuning issue.")
print()
k_needed = 0.05
for stop in (0.0005,0.001,0.002,0.005,0.01):
    print(f"  stop {stop*100:5.2f}%  -> max notional/equity for a 5% single-loss = {k_needed/stop:7.1f}x")
print()

print("=== 2. WHAT GROWTH PER TRADE IS NEEDED ===")
for n in (10,20,40,100,200):
    g=math.exp(math.log(8.0)/n)-1
    print(f"  {n:4d} trades/month -> need mean +{g*100:6.3f}% equity per trade (geometric)")
print()

print("=== 3. TRANSLATE TO REQUIRED ASSET-MOVE EDGE ===")
print("  with notional/equity = k, need mean asset return per trade = need/k")
for stop in (0.001,0.002,0.005):
    k=0.05/stop
    for n in (40,200):
        g=math.exp(math.log(8.0)/n)-1
        print(f"  stop {stop*100:.2f}% k={k:5.1f}x  n={n:3d} -> mean asset move needed {g/k*100:7.4f}%")
print()

print("=== 4. THE COST WALL (real broker costs) ===")
# realistic institutional/retail-ECN round-trip costs as fraction of notional
costs={'EURUSD':0.00002,'AUDUSD':0.000035,'XAUUSD':0.00007}
print("  round-trip cost as % of notional: EUR 0.0020%, AUD 0.0035%, XAU 0.0070% (ECN typical)")
for stop in (0.001,0.002,0.005):
    k=0.05/stop
    c=np.mean(list(costs.values()))
    print(f"  stop {stop*100:.2f}% k={k:5.1f}x -> cost per trade = {c*k*100:6.3f}% of EQUITY")
