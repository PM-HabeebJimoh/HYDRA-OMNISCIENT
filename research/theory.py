#!/usr/bin/env python3
"""THE GOVERNING EQUATION for monthly ROI at optimal leverage.

At Kelly sizing k* = mu/sigma^2, max log-growth per trade = SR^2/2.
Over N trades in a month:   log(1+ROI) = N * SR^2 / 2

So:  ROI_monthly = exp(N * SR^2 / 2) - 1

TWO LEVERS ONLY: N (trades/month) and SR (per-trade Sharpe).
Leverage is NOT a lever - it is already optimised out. This is why every
leverage sweep I ran returned nothing.
"""
import numpy as np, math
print("="*92); print("ROI_monthly = exp(N x SR^2 / 2) - 1"); print("="*92)
print(f"\n  Need ROI>1000% -> N x SR^2/2 > ln(11) = {math.log(11):.3f}")
print(f"  => N x SR^2 > {2*math.log(11):.3f}\n")
print(f"  {'N/month':>9} {'SR needed':>11} {'  what that means':<40}")
for N in (85,255,350,700,1400,2800,5600):
    sr=math.sqrt(2*math.log(11)/N)
    print(f"  {N:9d} {sr:11.4f}   {'3 assets 1 config' if N==255 else ''}")
print()
print("  MEASURED per-trade Sharpe of the Agba Metta magnitude bracket:")
print("    gold 4H w1.0 h3 : SR = 0.1063/1.0212 = 0.104")
print("    pooled Jan      : SR = 3.47/sqrt(346)= 0.187")
print()
print(f"  {'SR':>7} {'N needed for 1000%/mo':>24}")
for sr in (0.08,0.10,0.104,0.12,0.15,0.187,0.25):
    print(f"  {sr:7.3f} {2*math.log(11)/sr**2:24.0f}")
print()
print("="*92); print("THE KEY INSIGHT I MISSED FOR 14 SESSIONS"); print("="*92)
print("  log-growth is LINEAR in N, not sqrt.")
print("  Sharpe scales sqrt(N_eff) -- but ROI at Kelly scales exp(N_eff x SR^2/2).")
print("  Doubling independent streams DOUBLES the exponent.")
print()
print("  I have 3 assets x 2 timeframes x 3 widths x 2 holds = 36 candidate streams")
print("  ALREADY BUILT from verified bars. Never ran them as ONE Kelly portfolio.")
print()
print(f"  {'streams':>8} {'N_eff':>7} {'N/mo':>7} {'exponent':>10} {'monthly ROI':>16}")
for ns,neff_frac in ((1,1.0),(3,0.53),(6,0.5),(12,0.45),(24,0.40),(36,0.35)):
    neff=ns*neff_frac
    N=85*neff          # 85 trades/mo per effective stream
    ex=N*0.104**2/2
    print(f"  {ns:8d} {neff:7.2f} {N:7.0f} {ex:10.3f} {(math.exp(ex)-1)*100:15,.1f}%")
