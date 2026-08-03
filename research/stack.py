#!/usr/bin/env python3
"""STACK THE LEVERS. Same verified edge, multiplied by structure not prediction.

L2 magnitude edge (gold 4H bracket, t=+2.70, bias-audited)
 x L4 diversification across every instrument I actually have
 x L5 margin denominator instead of full notional

Everything below is measured on real bars. No new prediction claimed.
"""
import sys, json, glob, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
p1=load_1h(); p4=resample_4h(p1)
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035,
      'GBPUSD':0.00003,'USDCAD':0.00004}
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
def bracket(panel,a,w=1.0,hold=3):
    """WORST-CASE whipsaw handling (the honest one)."""
    ks,o,h,l,c=arr(panel,a); av=atr(h,l,c,20); n=len(c); out=[]
    cost=COST.get(a,0.00005)
    for i in range(21,n-hold):
        if np.isnan(av[i]): continue
        A_=av[i]/o[i]; up=o[i]*(1+w*A_); dn=o[i]*(1-w*A_)
        side=0; ent=None
        for j in range(i,min(i+hold,n)):
            hu=h[j]>=up; hd=l[j]<=dn
            if hu and hd:
                out.append((ks[i],-(2*w*A_)-2*cost)); side=-99; break
            if hu: side=+1; ent=up; break
            if hd: side=-1; ent=dn; break
        if side in (0,-99): continue
        ex=c[min(i+hold-1,n-1)]
        g=(ex-ent)/ent if side>0 else (ent-ex)/ent
        out.append((ks[i],g-2*cost))
    return out

# --- build the widest 4H panel I actually have verified bars for ---
H1x=collections.defaultdict(dict)
for f in glob.glob('data/raw/intraday_x/*_1h.json'):
    j=json.load(open(f)); s=j['symbol']
    for i,t in enumerate(j['t']):
        H1x[t][s]={'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}
def resample(p,secs,syms):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%secs)
        for s in syms:
            if s not in p[t]: continue
            d=p[t][s]
            if s not in B[b]: B[b][s]=dict(d)
            else:
                x=B[b][s]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return B
X4=resample(H1x,14400,('GBPUSD','USDCAD'))
X4={t:v for t,v in X4.items() if len(v)==2}

print("="*94)
print("L2 x L4 — SAME BRACKET, WIDER UNIVERSE (all verified bars)")
print("="*94)
streams={}
for a in ('gold','eur','aud'):
    ev=bracket(p4,a); streams[a]=ev
    g=np.array([e[1] for e in ev])
    print(f"  {a:>7}: n={len(g):4d} mean={g.mean()*100:+.4f}% t={g.mean()/(g.std()/np.sqrt(len(g))):+6.2f}")
for a in ('GBPUSD','USDCAD'):
    ev=bracket(X4,a)
    if len(ev)<30: print(f"  {a:>7}: n={len(ev)} too few"); continue
    streams[a]=ev
    g=np.array([e[1] for e in ev])
    print(f"  {a:>7}: n={len(g):4d} mean={g.mean()*100:+.4f}% t={g.mean()/(g.std()/np.sqrt(len(g))):+6.2f}")

# --- equal-risk portfolio across streams, chronological ---
allev=[]
for a,ev in streams.items():
    for ts,g in ev: allev.append((ts,a,g))
allev.sort()
g=np.array([e[2] for e in allev])
print(f"\n  POOLED PORTFOLIO: n={len(g)} mean={g.mean()*100:+.4f}% "
      f"t={g.mean()/(g.std()/np.sqrt(len(g))):+.2f}")
# measure diversification actually achieved
byday=collections.defaultdict(list)
for ts,a,x in allev:
    byday[datetime.datetime.fromtimestamp(int(ts),datetime.timezone.utc).strftime('%Y-%m-%d')].append(x)
dz=np.array([np.mean(v) for v in byday.values()])
sing=np.array([e[1] for e in streams['gold']])
print(f"  daily-aggregated portfolio Sharpe (ann) = {dz.mean()/dz.std()*np.sqrt(252):.2f}")
print(f"  gold-only Sharpe (ann, per-trade basis) = {sing.mean()/sing.std()*np.sqrt(252/ (len(sing)/8/21)):.2f}")

print()
print("="*94)
print("L5 — THE DENOMINATOR, APPLIED TO THE POOLED PORTFOLIO")
print("="*94)
ann=(1+g.mean())**len(g)-1
print(f"  pooled 8-month gross return at 1x notional = {ann*100:,.2f}%")
print()
print(f"  {'you post':>26} {'margin':>8} {'8-mo ROI on posted capital':>30}")
for nm,m in (("full notional (retail spot)",1.00),("FX prime broker 2%",0.02),
             ("CME gold futures ~5%",0.05),("CME FX futures ~3%",0.03)):
    # cap leverage at the level where worst single trade < 50% of posted margin
    worst=abs(g.min())
    maxlev=0.5/worst
    lev=min(1/m,maxlev)
    eq=np.cumprod(1+g*lev)
    pk=np.maximum.accumulate(eq); dd=((eq-pk)/pk).min()*100
    print(f"  {nm:>26} {m*100:7.1f}% {(eq[-1]-1)*100:20,.2f}%  (lev {lev:.0f}x, DD {dd:.1f}%)")
print()
print("  Leverage is capped so the WORST observed single trade costs <50% of margin.")
print("  That is a hard survivability constraint, not an optimisation.")
