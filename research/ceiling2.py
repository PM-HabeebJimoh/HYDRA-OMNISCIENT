"""The decisive number: what fraction of PERFECT FORESIGHT does the goal demand?"""
import numpy as np, math
from research.data import panels
P=panels()
TARGET=math.log(8.0); DDCAP=math.log(1/0.95)
MO=202/21.0  # ~9.6 months of data

def mdd(x):
    c=np.cumsum(x); return (np.maximum.accumulate(c)-c).max()

for tf,perbar_mo in (('D1',21),('H4',105),('H1',390)):
    d=P[tf]; O,C=d['O'],d['C']
    r=(C-O)/O; b=r.mean(1)
    N=perbar_mo
    # Required per-bar Sharpe for target with DD<5% (from requirement.py fit)
    mu_req=TARGET/N
    # binary-search sigma s.t. P(DD<cap)=95% -> approx sigma from earlier table; recompute
    rng=np.random.default_rng(1); lo,hi=1e-6,0.5
    for _ in range(35):
        s=(lo+hi)/2
        x=rng.normal(mu_req,s,size=(3000,N))
        cc=np.cumsum(x,1); p=((np.maximum.accumulate(cc,1)-cc).max(1)<DDCAP).mean()
        if p<0.95: hi=s
        else: lo=s
    sr_req=mu_req/lo
    # perfect foresight per-bar Sharpe on this data
    pf=np.abs(b); sr_pf=pf.mean()/pf.std()
    # accuracy needed: mu=(2a-1)E|b|, sd~=sd(b)
    a_req=0.5+ sr_req*b.std()/(2*pf.mean())
    print(f"{tf}: need per-bar SR {sr_req:.3f} | perfect-foresight SR {sr_pf:.3f} "
          f"| = {sr_req/sr_pf*100:5.1f}% of PERFECT | required directional accuracy {a_req*100:5.1f}%")
print()
print("Also: the max monthly return achievable at DD<=5% WITH PERFECT FORESIGHT,")
print("sizing so worst single-bar loss is impossible (no losses at all):")
for tf,n in (('D1',21),('H4',105),('H1',390)):
    d=P[tf]; b=((d['C']-d['O'])/d['O']).mean(1)
    e=np.abs(b).mean()
    print(f"  {tf}: perfect sign, k=notional/eq. return/mo = (1+k*{e*100:.4f}%)^{n}")
    for k in (5,10,25,50):
        print(f"      k={k:3d}x -> {( (1+k*e)**n -1)*100:14,.1f}% /mo   (DD=0 since never wrong)")
