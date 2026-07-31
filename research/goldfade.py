"""XAUUSD 'AM-align FADE' = 57.94% on n=214 (2025-01 -> 2026-07), CI excludes 50%.
This is the ONLY candidate with real history. Stress it properly."""
import json,math
import numpy as np
D=json.load(open('/tmp/allpairs.json'))
CORE=('XAUUSD','EURUSD','AUDUSD')
ds=sorted(d for d in D if all(s in D[d] for s in CORE))
o={s:np.array([D[d][s]['o'] for d in ds]) for s in CORE}
c={s:np.array([D[d][s]['c'] for d in ds]) for s in CORE}
r={s:(c[s]-o[s])/o[s] for s in CORE}
n=len(ds); print(f"{n} bars {ds[0]} -> {ds[-1]}")
al=np.sign(np.array([np.sign(r[s]) for s in CORE]).sum(0))
fire=np.abs(np.array([np.sign(r[s]) for s in CORE]).sum(0))==3
gold=r['XAUUSD']
sig=-al[:-1]                      # FADE
nx=np.sign(gold[1:])
m=fire[:-1]&(nx!=0)
k=int((sig[m]==nx[m]).sum()); N=int(m.sum())
print(f"\nFULL SAMPLE: {k}/{N} = {k/N*100:.2f}%")

# by year
for yr in ('2025','2026'):
    sel=m&np.array([d.startswith(yr) for d in ds[:-1]])
    if sel.sum()>10:
        kk=int((sig[sel]==nx[sel]).sum()); nn=int(sel.sum())
        print(f"  {yr}: {kk}/{nn} = {kk/nn*100:.2f}%")
# by half
half=n//2
for lab,sel in (('H1',m&(np.arange(n-1)<half)),('H2',m&(np.arange(n-1)>=half))):
    kk=int((sig[sel]==nx[sel]).sum()); nn=int(sel.sum())
    print(f"  {lab} ({ds[0] if lab=='H1' else ds[half]}..): {kk}/{nn} = {kk/nn*100:.2f}%")
# by quarter
print("\n  quarter-by-quarter:")
import collections
q=collections.defaultdict(lambda:[0,0])
for i in np.where(m)[0]:
    key=ds[i][:4]+'Q'+str((int(ds[i][5:7])-1)//3+1)
    q[key][1]+=1; q[key][0]+= int(sig[i]==nx[i])
for key in sorted(q):
    kk,nn=q[key]; print(f"    {key}: {kk:3d}/{nn:3d} = {kk/nn*100:5.1f}%")

# --- is it just gold mean-reversion, or does alignment add anything?
own=-np.sign(gold[:-1])
m2=(np.sign(gold[:-1])!=0)&(nx!=0)
k2=int((own[m2]==nx[m2]).sum()); n2=int(m2.sum())
print(f"\nCONTROL - plain gold FADE (no alignment needed): {k2}/{n2} = {k2/n2*100:.2f}%")
print(f"          alignment version:                      {k}/{N} = {k/N*100:.2f}%")
print(f"  -> alignment adds {(k/N-k2/n2)*100:+.2f} percentage points")

# --- economic value with real costs
mag=np.abs(gold[1:])
pnl=np.where(sig[m]==nx[m], np.abs(gold[1:][m]), -np.abs(gold[1:][m]))
print(f"\nmean per-trade gold move captured: {pnl.mean()*100:+.4f}%  (t={pnl.mean()/(pnl.std()/np.sqrt(N)):+.2f})")
cost=0.00007
print(f"after 0.7bp round-trip cost:      {(pnl.mean()-cost)*100:+.4f}%")
# max size at DD<5%
best=None
for kk in np.arange(0.1,40,0.1):
    net=pnl*kk-cost*kk; eq=np.cumprod(1+net)
    dd=((eq-np.maximum.accumulate(eq))/np.maximum.accumulate(eq)).min()
    if dd>-0.05: best=(kk,eq[-1],dd)
if best:
    months=n/21.0
    print(f"max size at DD<5%: k={best[0]:.1f}x -> total x{best[1]:.3f} over {months:.1f} months"
          f" = {(best[1]**(1/months)-1)*100:+.2f}%/month, DD {best[2]*100:.2f}%")

# --- selection-noise check: how many of the ~200 tests I ran would look this good?
print(f"\nNOTE: this was 1 of ~200 (currency x signal x filter) tests reported.")
z=(k/N-0.5)/math.sqrt(0.25/N); p=2*(1-0.5*(1+math.erf(abs(z)/math.sqrt(2))))
print(f"  raw p = {p:.4f};  Bonferroni over 200 tests needs p < {0.05/200:.2e} -> {'SURVIVES' if p<0.05/200 else 'FAILS'}")
