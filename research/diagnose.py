#!/usr/bin/env python3
"""FULL DIAGNOSIS of the real Agba Metta. Every claim measured."""
import sys, json, datetime, collections, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h(); p4=resample_4h(p1)
def daily(p):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%86400)
        for a in A:
            d=p[t][a]
            if a not in B[b]: B[b][a]=dict(d)
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
PAN={'DAILY':daily(p1),'4H':p4,'1H':p1}

print("="*96); print("PROBLEM 1 — THE SIGNAL HAS NO PREDICTIVE POWER"); print("="*96)
for tf,P in PAN.items():
    ks=sorted(P); hit=tot=0; rets=[]
    for i in range(len(ks)-1):
        s=P[ks[i]]
        up=all(s[a]['close']>s[a]['open'] for a in A)
        dn=all(s[a]['close']<s[a]['open'] for a in A)
        if not(up or dn): continue
        d=1 if up else -1
        nb=P[ks[i+1]]
        r=np.mean([ (nb[a]['close']-nb[a]['open'])/nb[a]['open'] for a in A])*d
        rets.append(r); tot+=1; hit+= (r>0)
    r=np.array(rets)
    print(f"  {tf:>5}: {tot:4d} signals  next-candle accuracy {hit/tot*100:5.2f}%  "
          f"mean {r.mean()*100:+.4f}%  t={r.mean()/(r.std()/np.sqrt(len(r))):+5.2f}")
print("  A coin flip is 50%. The signal carries no directional information.\n")

print("="*96); print("PROBLEM 2 — THE SIZING IS MATHEMATICALLY SUICIDAL"); print("="*96)
print("  20% equity / 3 assets x 500x = 33.3x notional PER ASSET, 100x total.")
print(f"  {'adverse move':>14} {'loss on the basket':>22}")
for m in (0.001,0.003,0.005,0.01):
    print(f"  {m*100:13.1f}% {m*100*100:21.1f}%")
print("  A 1% stop on all three legs = -100% of equity. The stop cannot protect you.")
print("  The account dies before the stop is even reached.\n")

print("="*96); print("PROBLEM 3 — THE THREE ASSETS ARE ONE BET"); print("="*96)
ks=sorted(p4)
R=np.array([[ (p4[k][a]['close']-p4[k][a]['open'])/p4[k][a]['open'] for a in A] for k in ks])
C=np.corrcoef(R.T)
print("           gold     eur     aud")
for i,a in enumerate(A): print(f"  {a:>5} "+" ".join(f"{C[i,j]:7.3f}" for j in range(3)))
w=np.ones(3)/3; port=(R*w).sum(1).std(); naive=np.sqrt(((w*R.std(0))**2).sum())
print(f"  N_eff = {(naive/port)**2:.2f} independent bets, not 3.")
print("  'Diversifying' across 3 correlated USD shorts adds risk, not safety.\n")

print("="*96); print("PROBLEM 4 — ALIGNMENT SELECTS THE WORST MOMENT TO ENTER"); print("="*96)
for tf,P in PAN.items():
    ks=sorted(P); al=[]; no=[]
    for i in range(len(ks)-1):
        s=P[ks[i]]
        f=all(s[a]['close']>s[a]['open'] for a in A) or all(s[a]['close']<s[a]['open'] for a in A)
        nb=P[ks[i+1]]
        rng=np.mean([ (nb[a]['high']-nb[a]['low'])/nb[a]['open'] for a in A])
        (al if f else no).append(rng)
    al,no=np.array(al),np.array(no)
    print(f"  {tf:>5}: next-candle RANGE after alignment {al.mean()*100:.4f}% vs {no.mean()*100:.4f}% "
          f"({al.mean()/no.mean():.3f}x)")
print("  Alignment predicts BIGGER moves - i.e. HIGHER stop-out probability.")
print("  The model uses a volatility signal to place a fixed 1% stop. Backwards.\n")

print("="*96); print("PROBLEM 5 — STOP-OUT RATE UNDER THE REAL MODEL"); print("="*96)
for tf,P in PAN.items():
    ks=sorted(P); st=tot=0
    for i in range(len(ks)-1):
        s=P[ks[i]]
        up=all(s[a]['close']>s[a]['open'] for a in A); dn=all(s[a]['close']<s[a]['open'] for a in A)
        if not(up or dn): continue
        d=1 if up else -1; nb=P[ks[i+1]]
        for a in A:
            en=nb[a]['open']; tot+=1
            if d>0 and nb[a]['low']<=en*0.99: st+=1
            if d<0 and nb[a]['high']>=en*1.01: st+=1
    print(f"  {tf:>5}: {st}/{tot} legs stopped = {st/tot*100:.2f}%   each stop = -33.3% of equity")
