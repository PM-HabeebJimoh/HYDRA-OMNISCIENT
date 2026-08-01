#!/usr/bin/env python3
"""AUDIT MY OWN BRACKET TEST.

In research/reframe.py, when BOTH triggers were hit inside the same bar I wrote:
      if hit_up and hit_dn: side=0; break     # -> the trade was SKIPPED

With OHLC data I cannot know which trigger fired first. By SKIPPING those bars I
silently deleted exactly the whipsaw cases - the losses. That is survivorship
bias, and it gets worse the NARROWER the bracket, which is precisely where my
best t-stats appeared (width=0.25).

Quantify it: how many bars are ambiguous, and what happens under honest handling?
"""
import sys
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
def arr(panel,a):
    ks=sorted(panel)
    return (np.array(ks),np.array([panel[k][a]['open'] for k in ks]),
            np.array([panel[k][a]['high'] for k in ks]),
            np.array([panel[k][a]['low'] for k in ks]),
            np.array([panel[k][a]['close'] for k in ks]))
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a

def run(panel,a,w,hold,mode):
    """mode: 'skip'(my original, biased) | 'worst'(both hit = whipsawed both ways)
             | 'coin'(random which fired first)"""
    ks,o,h,l,c=arr(panel,a); av=atr(h,l,c,20); n=len(c)
    rng=np.random.default_rng(0); out=[]; amb=0; tot=0
    for i in range(21,n-hold):
        if np.isnan(av[i]): continue
        A_=av[i]/o[i]; up=o[i]*(1+w*A_); dn=o[i]*(1-w*A_)
        side=0; ent=None
        for j in range(i,min(i+hold,n)):
            hu=h[j]>=up; hd=l[j]<=dn
            if hu and hd:
                tot+=1; amb+=1
                if mode=='skip': side=0
                elif mode=='worst':
                    # entered one side, stopped at the other: loss = full width x2
                    out.append((-(2*w*A_)-2*COST[a]))
                    side=-99
                else:
                    side=+1 if rng.random()<0.5 else -1; ent=up if side>0 else dn
                break
            if hu: side=+1; ent=up; tot+=1; break
            if hd: side=-1; ent=dn; tot+=1; break
        if side in (0,-99): continue
        ex=c[min(i+hold-1,n-1)]
        g=(ex-ent)/ent if side>0 else (ent-ex)/ent
        out.append(g-2*COST[a])
    return np.array(out), amb, tot

print("="*96)
print("BRACKET BIAS AUDIT — how much of the 'edge' was created by skipping whipsaws?")
print("="*96)
print(f"{'TF':>4} {'asset':>6} {'w':>5} {'ambiguous':>10} {'  SKIP (my orig)':>22} {'  WORST-CASE':>20} {'  COIN-FLIP':>20}")
for tf,pan in (('1H',p1),('4H',p4)):
    for a in A:
        for w in (0.25,0.5,1.0):
            gs,amb,tot=run(pan,a,w,3,'skip')
            gw,_,_  =run(pan,a,w,3,'worst')
            gc,_,_  =run(pan,a,w,3,'coin')
            f=lambda g: f"t={g.mean()/(g.std()/np.sqrt(len(g))):+6.2f}" if len(g)>5 else "  n/a "
            pct=amb/max(tot,1)*100
            print(f"{tf:>4} {a:>6} {w:5.2f} {pct:9.1f}% "
                  f"{f(gs)+' m='+format(gs.mean()*100,'+.4f'):>22} "
                  f"{f(gw)+' m='+format(gw.mean()*100,'+.4f'):>20} "
                  f"{f(gc)+' m='+format(gc.mean()*100,'+.4f'):>20}")
print()
print("READ: 'ambiguous' = share of bars where BOTH triggers were touched in one bar.")
print("At width 0.25 this is large, and those are exactly the whipsaw losses.")
print("SKIP deletes them -> inflated t. WORST-CASE books them as a full double loss.")
print("Truth for a resting-stop bracket lies between WORST and COIN, never at SKIP.")
