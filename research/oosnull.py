"""Run the ENTIRE select-on-train / measure-on-test procedure on randomized data
200 times. If real data's OOS result sits inside the noise distribution, the
'>80% pairs' are a mirage produced by searching thousands of combos."""
import json,itertools
import numpy as np
R0=np.load('/tmp/R2026.npy'); meta=json.load(open('/tmp/R2026meta.json'))
SYMS=meta['syms']; n,m=R0.shape; split=n//2
TRIPS=list(itertools.combinations(range(m),3)); THS=(0.0,0.002,0.004,0.006)

def procedure(R):
    S=np.sign(R); idx=np.arange(n-1)
    cands=[]
    for trip in TRIPS:
        al=S[:,list(trip)].sum(1); fire=np.abs(al)==3
        st=np.abs(R[:,list(trip)]).mean(1)
        for th in THS:
            f=fire&(st>=th)
            for j in range(m):
                nx=S[1:,j]
                tr=(idx<split)&f[:-1]&(nx!=0)
                if tr.sum()<10: continue
                for mode in (1,-1):
                    sig=np.sign(al[:-1])*mode
                    a=(sig[tr]==nx[tr]).mean()
                    if a>=0.80: cands.append((a,trip,th,j,mode))
    cands.sort(key=lambda x:-x[0]); cands=cands[:20]
    te=[]
    for a,trip,th,j,mode in cands:
        al=S[:,list(trip)].sum(1); fire=np.abs(al)==3
        st=np.abs(R[:,list(trip)]).mean(1); f=fire&(st>=th)
        nx=S[1:,j]; ts=(idx>=split)&f[:-1]&(nx!=0)
        if ts.sum()<5: continue
        sig=np.sign(al[:-1])*mode
        te.append((sig[ts]==nx[ts]).mean())
    return (len(cands), np.mean(te) if te else np.nan,
            sum(1 for b in te if b>=0.80), len(te))

nc,act,n80,nt=procedure(R0)
print(f"REAL DATA : {nc} combos >=80% on train | mean OOS {act*100:.1f}% | {n80}/{nt} still >=80%\n")
rng=np.random.default_rng(31); res=[]
for _ in range(200):
    flip=rng.choice([-1,1],size=(n,1))       # flip whole days: preserves cross-pair correlation
    c,mo,k,t=procedure(R0*flip)
    if not np.isnan(mo): res.append((c,mo,k,t))
C=np.array([r[0] for r in res]); M=np.array([r[1] for r in res]); K=np.array([r[2] for r in res])
print(f"NOISE (200 runs of the SAME procedure on sign-randomized days):")
print(f"  combos >=80% on train : median {np.median(C):.0f}   (real: {nc})")
print(f"  mean OOS accuracy     : median {np.median(M)*100:.1f}%  95th {np.percentile(M,95)*100:.1f}%   (real: {act*100:.1f}%)")
print(f"  count still >=80% OOS : median {np.median(K):.0f}      (real: {n80})")
p=(M>=act).mean()
print(f"\n  p-value of real mean-OOS vs noise = {p:.3f}")
print(f"  VERDICT: {'REAL EDGE' if p<0.05 else 'INDISTINGUISHABLE FROM SELECTION NOISE'}")
