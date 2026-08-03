"""Honest out-of-sample test: is basket direction predictable at all?
Walk-forward, expanding window, logistic regression on causal features only."""
import numpy as np, math
from research.data import panels
P=panels()
rng=np.random.default_rng(3)

def feats(d):
    O,H,L,C=d['O'],d['H'],d['L'],d['C']
    r=(C-O)/O; b=r.mean(1)
    n=len(b)
    F=[]
    prev=lambda x,k: np.concatenate([np.full(k,np.nan),x[:-k]])
    F.append(prev(b,1)); F.append(prev(b,2)); F.append(prev(b,3))
    F.append(prev(np.convolve(b,np.ones(5)/5,'same'),1))
    for j in range(3): F.append(prev(r[:,j],1))
    rng_=(H-L)/O; F.append(prev(rng_.mean(1),1))
    # overnight gap: this bar's open vs prev close (KNOWN at entry)
    gap=np.full(n,np.nan); gap[1:]=((O[1:]-C[:-1])/C[:-1]).mean(1)
    F.append(gap)
    # alignment state of previous bar
    s=np.sign(r); F.append(prev(s.sum(1),1))
    X=np.column_stack(F)
    return X,b

def logit_fit(X,y,l2=1.0,iters=300):
    Xb=np.column_stack([np.ones(len(X)),X]); w=np.zeros(Xb.shape[1])
    for _ in range(iters):
        p=1/(1+np.exp(-Xb@w)); g=Xb.T@(p-y)+l2*np.r_[0,w[1:]]
        Hs=Xb.T@(Xb*(p*(1-p))[:,None])+l2*np.eye(Xb.shape[1])
        try: w-=np.linalg.solve(Hs,g)
        except np.linalg.LinAlgError: break
    return w
def logit_p(w,X): return 1/(1+np.exp(-(np.column_stack([np.ones(len(X)),X])@w)))

for tf in ('D1','H4','H1'):
    d=P[tf]; X,b=feats(d)
    ok=~np.isnan(X).any(1); X,b=X[ok],b[ok]
    mu,sd=X.mean(0),X.std(0)+1e-12; Xs=(X-mu)/sd
    y=(b>0).astype(float)
    n=len(y); start=int(n*0.4)
    preds=np.full(n,np.nan)
    for i in range(start,n):
        w=logit_fit(Xs[:i],y[:i])
        preds[i]=logit_p(w,Xs[i:i+1])[0]
    m=~np.isnan(preds)
    pr,yy,bb=preds[m],y[m],b[m]
    acc=((pr>0.5)==(yy>0.5)).mean()
    sgn=np.where(pr>0.5,1,-1); pnl=sgn*bb
    t=pnl.mean()/(pnl.std()/np.sqrt(len(pnl)))
    print(f"{tf}: OOS n={len(pnl)} acc={acc*100:5.2f}%  mean={pnl.mean()*100:+.5f}%  t={t:+.2f}")
    # confidence-filtered
    for th in (0.55,0.60,0.65):
        s=np.abs(pr-0.5)>(th-0.5)
        if s.sum()>10:
            a2=((pr[s]>0.5)==(yy[s]>0.5)).mean(); p2=np.where(pr[s]>0.5,1,-1)*bb[s]
            print(f"    |p-.5|>{th-0.5:.2f}: n={s.sum():4d} acc={a2*100:5.2f}% mean={p2.mean()*100:+.5f}% t={p2.mean()/(p2.std()/np.sqrt(s.sum())):+.2f}")
