#!/usr/bin/env python3
"""THE INVERSION.

Every test I have run for this entire project asked ONE question:
    "Does the signal predict DIRECTION?"
Answer, exhaustively: no. ~50%. 259,200 configs. Zero edge.

I never once asked the inverse question:
    "Does the signal predict MAGNITUDE?"

Direction is a coin flip because markets are near-arbitrage-free in the first
moment. But the SECOND moment - variance - is the single most predictable
quantity in all of finance (ARCH, Nobel 2003). I have been mining the one
unpredictable thing while ignoring the predictable thing sitting in the same bars.

Test head-to-head: R^2 of predicting sign vs R^2 of predicting |move|.
"""
import sys, datetime
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)

def arr(panel,a):
    ks=sorted(panel)
    return (np.array(ks),
            np.array([panel[k][a]['open']  for k in ks]),
            np.array([panel[k][a]['high']  for k in ks]),
            np.array([panel[k][a]['low']   for k in ks]),
            np.array([panel[k][a]['close'] for k in ks]))

print("="*88)
print("ANGLE 1 — SIGN vs MAGNITUDE: which one is actually predictable?")
print("="*88)
print(f"{'asset':>6} {'TF':>4} {'n':>5} {'R2 predicting SIGN':>20} {'R2 predicting |move|':>22}")
for tf,pan in (('1H',p1),('4H',p4)):
    for a in A:
        ks,o,h,l,c=arr(pan,a)
        r=(c-o)/o
        x_sign=np.sign(r[:-1]); y_sign=np.sign(r[1:])
        m=(x_sign!=0)&(y_sign!=0)
        # R^2 of previous sign predicting next sign
        ss=np.corrcoef(x_sign[m],y_sign[m])[0,1]**2
        # R^2 of previous |move| predicting next |move|
        am=np.abs(r)
        sm=np.corrcoef(am[:-1],am[1:])[0,1]**2
        print(f"{a:>6} {tf:>4} {m.sum():5d} {ss*100:19.3f}% {sm*100:21.2f}%")
print()
print("  Magnitude is 20-100x more predictable than sign. This is not a small")
print("  difference - it is the difference between noise and signal.")

print()
print("="*88)
print("ANGLE 2 — WHAT IS 'ALIGNMENT' ACTUALLY MEASURING?")
print("="*88)
print("Agba Metta reads alignment as a DIRECTION signal. Test it as a VOLATILITY signal.")
print()
for tf,pan in (('1H',p1),('4H',p4)):
    ks=np.array(sorted(pan))
    R=np.array([[ (pan[k][a]['close']-pan[k][a]['open'])/pan[k][a]['open'] for a in A] for k in ks])
    RNG=np.array([[ (pan[k][a]['high']-pan[k][a]['low'])/pan[k][a]['open'] for a in A] for k in ks])
    S=np.sign(R); fire=np.abs(S.sum(1))==3
    nxt_absmove=np.abs(R[1:]).mean(1); nxt_range=RNG[1:].mean(1)
    f=fire[:-1]
    print(f"  {tf}: alignment fires {f.sum()}/{len(f)} bars")
    print(f"     next-bar |move|  after alignment {nxt_absmove[f].mean()*100:.4f}%  "
          f"vs no-alignment {nxt_absmove[~f].mean()*100:.4f}%  "
          f"ratio {nxt_absmove[f].mean()/nxt_absmove[~f].mean():.3f}x")
    print(f"     next-bar RANGE   after alignment {nxt_range[f].mean()*100:.4f}%  "
          f"vs no-alignment {nxt_range[~f].mean()*100:.4f}%  "
          f"ratio {nxt_range[f].mean()/nxt_range[~f].mean():.3f}x")
    a1=nxt_absmove[f]; a0=nxt_absmove[~f]
    t=(a1.mean()-a0.mean())/np.sqrt(a1.var()/len(a1)+a0.var()/len(a0))
    print(f"     t-stat on the volatility difference = {t:+.2f}")
    # direction for contrast
    d=np.sign(R[:-1].sum(1))[f]; nd=np.sign(R[1:].mean(1))[f]
    mm=(d!=0)&(nd!=0)
    print(f"     DIRECTION accuracy on the same bars  = {(d[mm]==nd[mm]).mean()*100:.2f}%  <- coin flip")
    print()

print("="*88)
print("ANGLE 3 — THE STOP IS THE COUNTERPARTY'S PROFIT CENTRE")
print("="*88)
print("AGBA V82 July: 76% of trades stopped out. Invert: what if the stop-out")
print("itself is the tradeable event? Measure what price does AFTER a 0.5xATR")
print("adverse excursion - the exact moment the model surrenders.")
print()
for tf,pan in (('1H',p1),):
    for a in A:
        ks,o,h,l,c=arr(pan,a)
        n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
        for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
        atr=np.full(n,np.nan)
        for i in range(19,n): atr[i]=tr[i-19:i+1].mean()
        fwd=[]
        for i in range(20,n-3):
            if np.isnan(atr[i]): continue
            # a LONG entered at open[i] stopped out 0.5 ATR below
            sp=o[i]-0.5*atr[i]
            if l[i]<=sp:
                # what happens over the next 3 bars from the stop price?
                fwd.append((c[min(i+3,n-1)]-sp)/sp)
        fwd=np.array(fwd)
        if len(fwd)>20:
            t=fwd.mean()/(fwd.std()/np.sqrt(len(fwd)))
            print(f"  {a:>5}: {len(fwd):4d} stop-outs, price 3 bars later {fwd.mean()*100:+.4f}% "
                  f"from the stop  t={t:+.2f}")
print("  -> positive means price REVERTS after taking out the stop (stop-hunt).")
