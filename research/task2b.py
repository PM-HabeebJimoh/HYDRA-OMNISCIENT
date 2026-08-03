#!/usr/bin/env python3
"""Validate the magnitude bet and compute what it PAYS monthly."""
import sys, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p4=resample_4h(load_1h())
def atrs(P,a,n=20):
    ks=sorted(P); c=[P[k][a]['close'] for k in ks]; h=[P[k][a]['high'] for k in ks]; l=[P[k][a]['low'] for k in ks]
    tr=[h[0]-l[0]]+[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(c))]
    out=[None]*len(c)
    for i in range(n-1,len(c)): out[i]=sum(tr[i-n+1:i+1])/n
    return out
def run(P,w=1.0,hold=3,gate=False):
    ks=sorted(P); AV={a:atrs(P,a) for a in A}; ev=[]
    for i in range(21,len(ks)-hold):
        s=P[ks[i]]
        if gate and not(all(s[a]['close']>s[a]['open'] for a in A) or all(s[a]['close']<s[a]['open'] for a in A)): continue
        for a in A:
            av=AV[a][i]
            if av is None: continue
            o=P[ks[i+1]][a]['open']; A_=av/o
            up=o*(1+w*A_); dn=o*(1-w*A_); side=0; ent=None
            for j in range(i+1,min(i+1+hold,len(ks))):
                b=P[ks[j]][a]; hu=b['high']>=up; hd=b['low']<=dn
                if hu and hd: ev.append((ks[i],a,-2*w*A_-2*COST[a],A_)); side=-99; break
                if hu: side=1; ent=up; break
                if hd: side=-1; ent=dn; break
            if side in (0,-99): continue
            ex=P[ks[min(i+hold,len(ks)-1)]][a]['close']
            ev.append((ks[i],a,((ex-ent)/ent if side>0 else (ent-ex)/ent)-2*COST[a],A_))
    return ev
ev=run(p4,gate=False)
g=np.array([e[2] for e in ev]); sz=np.array([e[3] for e in ev])
T=lambda x: x.mean()/(x.std()/np.sqrt(len(x)))
print("="*94); print("MAGNITUDE BET — 4H bracket, width 1.0xATR, hold 3, ALL bars"); print("="*94)
print(f"  n={len(g)}  WR={(g>0).mean()*100:.2f}%  mean={g.mean()*100:+.4f}%  t={T(g):+.2f}")
h=len(g)//2
print(f"\n  SPLIT-HALF: first {T(g[:h]):+.2f}   second {T(g[h:]):+.2f}")
print("\n  MOVE-SIZE GATE (real edge grows with move size; bounce hides in small):")
q=np.quantile(sz,[0,.5,1.0])
for lo,hi,lab in ((q[0],q[1],'smaller half ATR'),(q[1],q[2],'larger half ATR')):
    m=(sz>=lo)&(sz<=hi); print(f"    {lab:<20} n={m.sum():5d} mean={g[m].mean()*100:+.4f}% t={T(g[m]):+.2f}")
print("\n  SIGN-FLIP NULL (kills edge, keeps magnitudes):")
rng=np.random.default_rng(7)
null=np.array([T(g*rng.choice([-1.0,1.0],len(g))) for _ in range(500)])
print(f"    actual t={T(g):+.2f}  null median {np.median(null):+.2f} 95th {np.percentile(null,95):+.2f}")
print(f"    p={(null>=T(g)).mean():.4f} -> {'REAL' if (null>=T(g)).mean()<0.05 else 'NOISE'}")
print("\n  MONTH BY MONTH:")
m=collections.defaultdict(list)
for t_,a,x,s in ev: m[utc(t_).strftime('%Y-%m')].append(x)
for k in sorted(m):
    x=np.array(m[k]); print(f"    {k}: n={len(x):4d} mean={x.mean()*100:+.4f}% t={T(x):+5.2f}")
print("\n"+"="*94); print("WHAT IT PAYS — monthly, Kelly-bounded"); print("="*94)
kel=g.mean()/g.var()
print(f"  full-Kelly leverage = {kel:.1f}x   worst single trade = {g.min()*100:.2f}%")
print(f"  {'sizing':>16} {'lev':>7} {'median monthly':>16} {'worst month':>13} {'8-mo':>14}")
for nm,f in (("quarter-Kelly",.25),("half-Kelly",.5),("full-Kelly",1.0)):
    lev=kel*f; eq=1.0; rois=[]
    for k in sorted(m):
        x=np.array(m[k]); s=eq
        step=1+x*lev
        if (step<=0).any(): rois.append(-100.0); eq=0; break
        eq*=np.prod(step); rois.append((eq/s-1)*100)
    print(f"  {nm:>16} {lev:6.1f}x {np.median(rois):15.1f}% {min(rois):12.1f}% {(eq-1)*100:13,.1f}%")
