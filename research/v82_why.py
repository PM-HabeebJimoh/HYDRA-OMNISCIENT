#!/usr/bin/env python3
"""WHY does V82 work where Agba Metta fails? Decompose, then apply real costs.
Also run the move-size gate that caught my bid-ask-bounce error."""
import sys, collections, bisect
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}   # round-trip frac of notional

def series(panel,a):
    ks=sorted(panel)
    return (np.array(ks),np.array([panel[k][a]['open'] for k in ks]),
            np.array([panel[k][a]['high'] for k in ks]),
            np.array([panel[k][a]['low'] for k in ks]),
            np.array([panel[k][a]['close'] for k in ks]))
def forecast(o,h,l,c):
    n=len(c); bp=(c>o).astype(float)
    ma20=np.full(n,np.nan); ma50=np.full(n,np.nan)
    for i in range(19,n): ma20[i]=c[i-19:i+1].mean()
    for i in range(49,n): ma50[i]=c[i-49:i+1].mean()
    pct=np.zeros(n); pct[1:]=(c[1:]-c[:-1])/c[:-1]
    r3=np.full(n,np.nan); stk=np.full(n,np.nan)
    for i in range(3,n): r3[i]=pct[i-2:i+1].sum()
    for i in range(2,n): stk[i]=bp[i-2:i+1].sum()
    return (c>ma20)&(ma20>ma50),(c<ma20)&(ma20<ma50),stk,r3
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a

def collect(fp,xp,mh=12,min_streak=2,smult=1.0,tmult=2.0,use_filters=(1,1,1)):
    ev=[]
    for a in A:
        xk,xo,xh,xl,xc=series(xp,a); fk,fo,fh,fl,fc=series(fp,a)
        tu,td,stk,r3=forecast(fo,fh,fl,fc); av=atr(xh,xl,xc,20)
        fkl=list(fk)
        for i in range(60,len(xc)-mh):
            j=bisect.bisect_right(fkl,xk[i])-1
            if j<60 or np.isnan(stk[j]) or np.isnan(r3[j]) or np.isnan(av[i]): continue
            ut,us,ur=use_filters
            up = (tu[j] or not ut) and (stk[j]>=min_streak or not us) and (r3[j]>0 or not ur)
            dn = (td[j] or not ut) and (stk[j]<=(3-min_streak) or not us) and (r3[j]<0 or not ur)
            d='BUY' if up and not dn else ('SELL' if dn and not up else None)
            if d is None: continue
            S=xc[i]; stop=S-smult*av[i] if d=='BUY' else S+smult*av[i]
            tgt =S+tmult*av[i] if d=='BUY' else S-tmult*av[i]
            ex=None
            for k in range(i+1,min(i+mh,len(xc))):
                if d=='BUY':
                    if xl[k]<=stop: ex=stop;break
                    if xh[k]>=tgt: ex=tgt;break
                else:
                    if xh[k]>=stop: ex=stop;break
                    if xl[k]<=tgt: ex=tgt;break
            if ex is None: ex=xc[min(i+mh,len(xc)-1)]
            gross=(ex-S)/S if d=='BUY' else (S-ex)/S
            ev.append((xk[i],a,gross,abs(S-stop)/S,av[i]/S))
    return ev

def summarise(ev,cost=True,lab=""):
    if not ev: print(f"  {lab}: none"); return
    R=[]; 
    for ts,a,g,rf,_ in ev:
        c=COST[a] if cost else 0.0
        R.append((g-c)/rf)          # net return expressed in R
    R=np.array(R)
    t=R.mean()/(R.std()/np.sqrt(len(R)))
    print(f"  {lab:<40} n={len(R):5d}  meanR={R.mean():+.4f}  WR={(R>0).mean()*100:5.2f}%  t={t:+6.2f}")
    return R

print("="*92); print("1. FILTER ABLATION (forecast 4H / exec 1H, gross)"); print("="*92)
for f,lab in (((1,1,1),'all three filters (V82 as specified)'),
              ((1,1,0),'trend + streak, no 3-bar return'),
              ((1,0,1),'trend + return, no streak'),
              ((0,1,1),'streak + return, no trend'),
              ((1,0,0),'trend only'),((0,1,0),'streak only'),((0,0,1),'return only')):
    summarise(collect(p4,p1,use_filters=f),cost=False,lab=lab)

print()
print("="*92); print("2. REAL COSTS APPLIED"); print("="*92)
ev=collect(p4,p1)
summarise(ev,cost=False,lab="gross")
Rn=summarise(ev,cost=True, lab="net of real spread")

print()
print("="*92); print("3. MOVE-SIZE GATE (the test that caught my bounce error)"); print("="*92)
sizes=np.array([e[4] for e in ev])
Rg=np.array([(e[2]-COST[e[1]])/e[3] for e in ev])
q=np.quantile(sizes,[0,.25,.5,.75,1.0])
for lo,hi,lab in ((q[0],q[1],'smallest 25% ATR'),(q[1],q[2],'25-50%'),(q[2],q[3],'50-75%'),(q[3],q[4],'largest 25% ATR')):
    m=(sizes>=lo)&(sizes<=hi); r=Rg[m]
    print(f"  {lab:<40} n={m.sum():5d}  meanR={r.mean():+.4f}  t={r.mean()/(r.std()/np.sqrt(len(r))):+6.2f}")
print("  -> a real trend edge should NOT be concentrated in the smallest bars.")

print()
print("="*92); print("4. R:R GEOMETRY — is 2:1 actually optimal here?"); print("="*92)
print(f"  {'stop x ATR':>11} {'target x ATR':>13} {'n':>6} {'WR':>7} {'meanR(net)':>11}")
for s in (0.5,1.0,1.5,2.0):
    for tm in (1.0,1.5,2.0,3.0):
        e=collect(p4,p1,smult=s,tmult=tm)
        if not e: continue
        R=np.array([(x[2]-COST[x[1]])/x[3] for x in e])
        print(f"  {s:11.1f} {tm:13.1f} {len(R):6d} {(R>0).mean()*100:6.2f}% {R.mean():+11.4f}")
