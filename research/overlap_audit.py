#!/usr/bin/env python3
"""AUDIT: are the 36 streams independent, or the SAME bet counted 12x?
3 assets x 2 TF x 3 widths x 2 holds -> the same gold bar feeds 12 streams.
If so, '73,400 trades' is inflated and the true N is far lower."""
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
print("="*96); print("STREAM OVERLAP AUDIT"); print("="*96)
print(f"  streams={len(keys)}  nominal trades={sum(len(v) for v in S.values()):,}")
# daily aggregate each stream
days=sorted({utc(t).strftime('%Y-%m-%d') for ev in S.values() for t,_ in ev})
D={}
for k,ev in S.items():
    m=collections.defaultdict(list)
    for t,g in ev: m[utc(t).strftime('%Y-%m-%d')].append(g)
    D[k]=np.array([np.mean(m[d]) if d in m else 0.0 for d in days])
M=np.column_stack([D[k] for k in keys])
C=np.corrcoef(M.T)
ev_=np.linalg.eigvalsh(C)[::-1]
neff=(ev_.sum()**2)/(ev_**2).sum()
print(f"  mean pairwise |corr| = {np.abs(C[np.triu_indices(len(keys),1)]).mean():.3f}")
print(f"  PC1 explains {ev_[0]/ev_.sum()*100:.1f}%")
print(f"  TRUE N_eff = {neff:.2f}  from {len(keys)} nominal streams")
print(f"  -> each nominal stream is worth {neff/len(keys):.3f} independent streams")
print()
print("  Same-asset correlation (should be HIGH = redundant):")
for a in A:
    idx=[i for i,k in enumerate(keys) if k.startswith(a+'|')]
    sub=C[np.ix_(idx,idx)]
    print(f"    {a}: {len(idx)} streams, mean |corr| = {np.abs(sub[np.triu_indices(len(idx),1)]).mean():.3f}")
print("  Cross-asset correlation (the only real diversification):")
cross=[]
for i,ki in enumerate(keys):
    for j,kj in enumerate(keys):
        if j<=i: continue
        if ki.split('|')[0]!=kj.split('|')[0]: cross.append(abs(C[i,j]))
print(f"    mean |corr| across different assets = {np.mean(cross):.3f}")
print()
print("="*96); print("WHAT THIS MEANS FOR THE ROI EQUATION"); print("="*96)
print("  ROI = exp(N_eff_trades x SR^2 / 2) - 1")
tot=sum(len(v) for v in S.values())
eff_trades=tot*(neff/len(keys))
print(f"  nominal trades      : {tot:,}")
print(f"  EFFECTIVE trades    : {eff_trades:,.0f}   (x{neff/len(keys):.3f})")
print(f"  per month           : {eff_trades/8:,.0f}")
sr=0.104
print(f"  exponent per month  = {eff_trades/8*sr**2/2:.3f}")
print(f"  implied monthly ROI = {(math.exp(eff_trades/8*sr**2/2)-1)*100:,.0f}%")
print()
print("  Compare: the 98.7% DD run got median +72.3%/month.")
print("  If the equation predicted far more, the shortfall IS the overlap.")
