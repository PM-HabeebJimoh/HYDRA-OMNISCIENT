#!/usr/bin/env python3
"""ANGLES 13-16 + combining the survivors."""
from research.a16_core import *

print("="*100); print("ANGLE 13 (COMBINATORIAL) — cross uncorrelated dimensions"); print("="*100)
print("  Lead-lag (A11) x time-of-day (A7) x vol regime (A10) — never combined.")
ks=np.array(sorted(p1))
R={a:np.array([(p1[k][a]['close']-p1[k][a]['open'])/p1[k][a]['open'] for k in ks]) for a in A}
hh=np.array([utc(t).hour for t in ks])
av={a:atr(np.array([p1[k][a]['high'] for k in ks]),
          np.array([p1[k][a]['low']  for k in ks]),
          np.array([p1[k][a]['close']for k in ks]),20) for a in A}
pairs=[('gold','eur'),('eur','aud'),('aud','eur')]
for src,dst in pairs:
    base=-np.sign(R[src][:-1])*R[dst][1:]-COST[dst]   # FADE (the significant sign)
    print(f"\n  {src}->{dst} FADE  base t={T(base):+.2f}")
    rows=[]
    for lo,hi,lab in ((0,7,'Asia 00-06'),(7,13,'London 07-12'),(13,18,'NY 13-17'),(18,24,'Late 18-23')):
        m=(hh[:-1]>=lo)&(hh[:-1]<hi)
        if m.sum()<80: continue
        rows.append((abs(T(base[m])),lab,base[m]))
    for _,lab,seg in sorted(rows,reverse=True):
        print(f"     {lab:<14} n={len(seg):5d} mean={seg.mean()*1e4:+7.3f}bp t={T(seg):+6.2f}")

print()
print("="*100); print("ANGLE 14 (SCALE INVARIANCE) — does it hold at every horizon?"); print("="*100)
print("  A real effect scales. An artifact appears at one horizon only.")
for src,dst in (('eur','aud'),):
    for tf,pan,lab in ((p1,p1,'1H'),):
        pass
for lag in (1,2,3,6,12):
    seg=-np.sign(R['eur'][:-lag])*R['aud'][lag:]-COST['aud']
    print(f"  eur->aud FADE at lag {lag:2d} bar(s): mean={seg.mean()*1e4:+7.3f}bp t={T(seg):+6.2f}")

print()
print("="*100); print("ANGLE 15 (ADVERSARIAL) — what would break this?"); print("="*100)
print("  Test: is eur->aud lead-lag just BOTH loading on the same USD factor?")
usd=(R['eur']+R['aud'])/2
resid_aud=R['aud']-np.polyval(np.polyfit(usd,R['aud'],1),usd)
seg=-np.sign(R['eur'][:-1])*resid_aud[1:]
print(f"  after removing common USD factor from AUD: t={T(seg):+.2f}")
print("  Test: same-bar correlation (is t+1 just contemporaneous leakage?)")
print(f"  corr(eur_t, aud_t)   = {np.corrcoef(R['eur'],R['aud'])[0,1]:+.3f}")
print(f"  corr(eur_t, aud_t+1) = {np.corrcoef(R['eur'][:-1],R['aud'][1:])[0,1]:+.3f}")

print()
print("="*100); print("ANGLE 16 (SYNTHESIS) — stack every surviving angle"); print("="*100)
print("  Survivors: A2 magnitude(R2 8%) | A11 lead-lag fade | A7 session | A10 vol-expand")
sig=np.zeros(len(ks)-1)
n_sig=0
for src,dst in (('gold','eur'),('eur','aud'),('aud','eur')):
    sig=sig+(-np.sign(R[src][:-1]))
    n_sig+=1
sig=sig/n_sig
# trade AUD+EUR basket on the consensus fade signal, gated by session+vol
basket_next=(R['eur'][1:]+R['aud'][1:])/2
cost=(COST['eur']+COST['aud'])/2
london=(hh[:-1]>=7)&(hh[:-1]<18)
volx=np.zeros(len(ks),dtype=bool)
for i in range(40,len(ks)):
    m=np.nanmean([av[a][i] for a in A]); pm=np.nanmean([np.nanmean(av[a][i-20:i]) for a in A])
    volx[i]= m>pm*1.02
strong=np.abs(sig)>=0.9
combos=[("consensus fade, all bars",np.ones(len(sig),bool)),
        ("+ strong consensus (all 3 agree)",strong),
        ("+ London/NY session",strong&london),
        ("+ vol expanding",strong&london&volx[:-1])]
for lab,m in combos:
    if m.sum()<50: print(f"  {lab:<44} n={m.sum()} too few"); continue
    pnl=np.sign(sig[m])*basket_next[m]-cost
    rep(f"  {lab}",pnl)
