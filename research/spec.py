#!/usr/bin/env python3
"""THE SPEC: WR>80%, ROI>1000%, DD<8%. What does it DEMAND, arithmetically?"""
import numpy as np, math
print("="*94); print("DECODING THE SPEC BEFORE SEARCHING"); print("="*94)
print("\n1. WIN RATE IS A FREE PARAMETER — it is set by GEOMETRY, not by skill.")
print("   On a driftless walk, P(hit target before stop) = stop/(stop+target).")
print(f"   {'target WR':>10} {'stop/target ratio needed':>26}")
for wr in (0.5,0.6,0.7,0.8,0.9):
    print(f"   {wr*100:9.0f}% {wr/(1-wr):25.1f}x")
print("   -> 80% WR requires stop = 4x target. This is FREE. Anyone can have 80% WR.")
print("   -> On a fair walk expectancy is EXACTLY zero at every WR. WR alone is meaningless.")
print("\n2. THE REAL CONSTRAINT IS THE RETURN/DD RATIO (MAR).")
print("   ROI>1000% with DD<8% over 8 months:")
print(f"   MAR = 1000/8 = {1000/8:.0f}")
print("   For reference: best CTAs run MAR 1-2. Medallion is ~3-5.")
print("   A MAR of 125 is ~25-40x the best track records in existence.")
print("\n3. WHAT SHARPE DOES MAR 125 IMPLY?")
print("   Rough: maxDD over a period ~ (0.5..1.0) x sigma_period / Sharpe-ish.")
print("   Simulate directly: what per-trade Sharpe is needed for 10x with DD<8%?")
rng=np.random.default_rng(0)
TARGET=math.log(11.0); DDCAP=math.log(1/0.92)
print(f"\n   {'trades':>7} {'needed mu/trade':>16} {'max sigma':>11} {'per-trade SR':>13} {'ann SR':>9}")
for N in (500,1000,2000,5000,10000):
    mu=TARGET/N; lo,hi=1e-7,0.5
    for _ in range(40):
        s=(lo+hi)/2
        x=rng.normal(mu,s,size=(2000,N))
        cc=np.cumsum(x,1)
        ok=((np.maximum.accumulate(cc,1)-cc).max(1)<DDCAP).mean()
        if ok<0.95: hi=s
        else: lo=s
    sr=mu/lo
    print(f"   {N:7d} {mu*100:15.4f}% {lo*100:10.4f}% {sr:13.4f} {sr*math.sqrt(N*1.5):8.2f}")
print("\n   -> The spec is a SHARPE requirement. WR is decoration.")
print("   -> More trades LOWERS the required per-trade Sharpe. N is the lever.")
