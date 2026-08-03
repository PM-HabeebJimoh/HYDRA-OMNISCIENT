"""Is the H4-gold survivor real, or the best of 2016 lottery tickets?
Empirical null: re-run the FULL grid on sign-randomized returns, record max |t|."""
import numpy as np, math
from research.data import panels
P=panels()

def grid_max_t(d_by_tf,rng=None):
    best=0.0
    for tf,d in d_by_tf.items():
        O,Hi,Lo,C=d['O'],d['H'],d['L'],d['C']
        r=(C-O)/O
        if rng is not None:
            flip=rng.choice([-1,1],size=(len(r),1))   # flip whole bars: keeps cross-asset corr
            r=r*flip
        for H in (1,2,3,5):
            for minstr in (0.0,0.001,0.003):
                for sub in [(0,1,2),(0,1),(0,2),(1,2),(0,),(1,),(2,)]:
                    idx=list(sub); s=np.sign(r[:,idx])
                    fire=(np.abs(s.sum(1))==len(idx))&(np.abs(r[:,idx]).mean(1)>=minstr)
                    fire[len(r)-H-1:]=False
                    if fire.sum()<15: continue
                    i=np.where(fire)[0]; dirn=s[i,0]
                    fwd=np.array([r[j+1:j+1+H,idx].sum(0).mean() for j in i])
                    a=dirn*fwd
                    t=a.mean()/(a.std()/np.sqrt(len(a))+1e-12)
                    best=max(best,abs(t))
    return best

D={tf:P[tf] for tf in ('D1','H4','H1')}
actual=grid_max_t(D)
rng=np.random.default_rng(21)
null=[grid_max_t(D,rng) for _ in range(200)]
null=np.array(null)
print(f"actual grid max|t| (no-stop approximation) = {actual:.2f}")
print(f"null max|t|: median {np.median(null):.2f}  95th {np.percentile(null,95):.2f}  max {null.max():.2f}")
print(f"p-value of the BEST config after selection = {(null>=actual).mean():.3f}")
print()
print(f"H4-gold candidate t=+3.37 vs null 95th pct {np.percentile(null,95):.2f}"
      f" -> {'REAL' if 3.37>np.percentile(null,95) else 'INDISTINGUISHABLE FROM SELECTION NOISE'}")
