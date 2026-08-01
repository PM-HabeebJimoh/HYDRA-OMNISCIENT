#!/usr/bin/env python3
"""WHY exp(N x SR^2/2) OVER-PREDICTS BY 72,000x.

The formula ROI = exp(N x SR^2/2) assumes trades are SEQUENTIAL - each one
resolves and compounds before the next begins. Then Kelly per trade is optimal.

My 36 streams trade SIMULTANEOUSLY. When k streams are open at once you are
holding k concurrent positions. Portfolio variance is NOT the sum of individual
variances - correlated bets add variance faster than they add return.

Correct treatment: PORTFOLIO Kelly on the covariance matrix.
  optimal exponent per period = SR_portfolio^2 / 2   (NOT N x SR_single^2/2)

Summing per-stream Kelly fractions on correlated streams = massive over-betting.
That is exactly what produced 98.7% DD.
"""
import sys, datetime, collections, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
p1=load_1h(); p4=resample_4h(p1)
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
def arr(P,a):
    ks=sorted(P); return (np.array(ks),*(np.array([P[k][a][f] for k in ks]) for f in ('open','high','low','close')))
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a
def stream(P,a,w,hold):
    ks,o,h,l,c=arr(P,a); av=atr(h,l,c,20); n=len(c); out=[]
    for i in range(21,n-hold):
        if np.isnan(av[i]): continue
        A_=av[i]/o[i]; up=o[i]*(1+w*A_); dn=o[i]*(1-w*A_); s=0; e=None
        for j in range(i,min(i+hold,n)):
            hu=h[j]>=up; hd=l[j]<=dn
            if hu and hd: out.append((ks[i],-2*w*A_-2*COST[a])); s=-99; break
            if hu: s=1;e=up;break
            if hd: s=-1;e=dn;break
        if s in (0,-99): continue
        ex=c[min(i+hold-1,n-1)]
        out.append((ks[i],((ex-e)/e if s>0 else (e-ex)/e)-2*COST[a]))
    return out
S={}
for a in A:
    for P,tf in ((p4,'4H'),(p1,'1H')):
        for w in (0.5,0.75,1.0):
            for hold in (3,6):
                ev=stream(P,a,w,hold)
                if len(ev)>=100: S[f"{a}|{tf}|w{w}|h{hold}"]=ev
keys=list(S)
days=sorted({utc(t).strftime('%Y-%m-%d') for ev in S.values() for t,_ in ev})
D={}
for k,ev in S.items():
    m=collections.defaultdict(list)
    for t,g in ev: m[utc(t).strftime('%Y-%m-%d')].append(g)
    D[k]=np.array([np.sum(m[d]) if d in m else 0.0 for d in days])  # SUM = daily P&L at 1x
M=np.column_stack([D[k] for k in keys])
print("="*96); print("CONCURRENCY CHECK — how many streams are live at once?"); print("="*96)
live=(M!=0).sum(1)
print(f"  trading days={len(days)}  mean streams active per day = {live.mean():.1f} of {len(keys)}")
print(f"  -> trades are CONCURRENT, not sequential. Kelly-per-trade is invalid.")
print()
print("="*96); print("CORRECT PORTFOLIO KELLY (covariance-aware)"); print("="*96)
mu=M.mean(0); Sig=np.cov(M.T)
# regularise
Sig_r=Sig+np.eye(len(keys))*1e-10
try:
    wk=np.linalg.solve(Sig_r,mu)      # Kelly weights = Sigma^-1 mu
except Exception:
    wk=np.linalg.pinv(Sig_r)@mu
port_daily=M@wk
sr_port=port_daily.mean()/port_daily.std()*math.sqrt(252)
print(f"  portfolio ann Sharpe at full Kelly weights = {sr_port:.2f}")
print(f"  theoretical max monthly log-growth = SR^2/24 = {sr_port**2/24:.4f}")
print(f"  => theoretical max monthly ROI = {(math.exp(sr_port**2/24)-1)*100:,.1f}%")
print()
print("  Note: this is FULL Kelly - maximal growth, ~50%+ drawdowns by construction.")
print()
print("="*96); print("EQUAL-RISK vs KELLY-WEIGHTED — realistic sizing"); print("="*96)
eq_w=np.ones(len(keys))/len(keys)
for nm,w in (("equal weight",eq_w),("Kelly weights",wk/np.abs(wk).sum())):
    pd_=M@w
    s=pd_.mean()/pd_.std()*math.sqrt(252)
    print(f"  {nm:<16} ann Sharpe {s:6.2f}   max monthly ROI at full Kelly = {(math.exp(s**2/24)-1)*100:8,.1f}%")
print()
print("="*96); print("THE REAL CEILING FOR THIS SIGNAL"); print("="*96)
print("  ROI_monthly(max) = exp(SR_ann^2 / 24) - 1        [portfolio Kelly, concurrent]")
print(f"\n  {'ann Sharpe':>11} {'max monthly ROI':>18}")
for s in (1,2,3,5,8,10,13,17,20):
    print(f"  {s:11.1f} {(math.exp(s**2/24)-1)*100:17,.1f}%")
need=math.sqrt(24*math.log(11))
print(f"\n  For >1000%/month you need ann Sharpe = {need:.2f}")
print(f"  measured (equal-weight, this portfolio) = {(M@eq_w).mean()/(M@eq_w).std()*math.sqrt(252):.2f}")
