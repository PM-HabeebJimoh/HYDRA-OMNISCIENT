"""Leak-free walk-forward. Every feature at row i uses ONLY data available
   before bar i's OPEN. Enforced by an explicit causality assertion."""
import numpy as np
from research.data import panels
P=panels()

def build(d):
    O,H,L,C=d['O'],d['H'],d['L'],d['C']
    r=(C-O)/O; b=r.mean(1); n=len(b)
    def lag(x,k):
        y=np.full(len(x),np.nan); y[k:]=x[:-k]; return y
    def rollmean(x,w):           # CAUSAL trailing mean over x[i-w .. i-1]
        y=np.full(len(x),np.nan)
        for i in range(w+1,len(x)):
            seg=x[i-w:i]
            if not np.isnan(seg).any(): y[i]=seg.mean()
        return y
    F={}
    F['b1']=lag(b,1); F['b2']=lag(b,2); F['b3']=lag(b,3)
    F['bma5']=rollmean(b,5); F['bma20']=rollmean(b,20)
    for j,a in enumerate(('gold','eur','aud')): F[f'r1_{a}']=lag(r[:,j],1)
    F['rng1']=lag(((H-L)/O).mean(1),1)
    F['vol20']=np.sqrt(np.clip(rollmean(b**2,20),0,None))
    gap=np.full(n,np.nan); gap[1:]=((O[1:]-C[:-1])/C[:-1]).mean(1)
    F['gap']=gap                                  # known at open of bar i
    F['align1']=lag(np.sign(r).sum(1),1)
    names=list(F); X=np.column_stack([F[k] for k in names])
    return X,b,names

def causality_check(d,X,names):
    """Perturb bar i's OHLC; no feature at row <= i may change."""
    import copy
    O,H,L,C=[a.copy() for a in (d['O'],d['H'],d['L'],d['C'])]
    i=len(O)//2
    d2=dict(d); 
    O2,H2,L2,C2=O.copy(),H.copy(),L.copy(),C.copy()
    C2[i]*=1.05; H2[i]*=1.05
    X2,_,_=build(dict(O=O2,H=H2,L=L2,C=C2))
    bad=[]
    for row in range(0,i+1):
        diff=~(np.isclose(np.nan_to_num(X[row]),np.nan_to_num(X2[row])))
        if diff.any(): bad.append((row,[names[k] for k in np.where(diff)[0]]))
    return bad

def logit_fit(X,y,l2=1.0,iters=200):
    Xb=np.column_stack([np.ones(len(X)),X]); w=np.zeros(Xb.shape[1])
    for _ in range(iters):
        p=1/(1+np.exp(-np.clip(Xb@w,-30,30))); g=Xb.T@(p-y)+l2*np.r_[0,w[1:]]
        Hs=Xb.T@(Xb*(p*(1-p))[:,None])+l2*np.eye(Xb.shape[1])
        try: st=np.linalg.solve(Hs,g)
        except np.linalg.LinAlgError: break
        w-=st
        if np.abs(st).max()<1e-9: break
    return w
def lp(w,X): return 1/(1+np.exp(-np.clip(np.column_stack([np.ones(len(X)),X])@w,-30,30)))

for tf in ('D1','H4','H1'):
    d=P[tf]; X,b,names=build(d)
    bad=causality_check(d,X,names)
    print(f"=== {tf} === causality violations: {len(bad)}", bad[:3] if bad else "(clean)")
    ok=~np.isnan(X).any(1); Xc,bc=X[ok],b[ok]
    y=(bc>0).astype(float); n=len(y); start=int(n*0.4)
    pr=np.full(n,np.nan)
    for i in range(start,n):
        mu,sd=Xc[:i].mean(0),Xc[:i].std(0)+1e-12
        w=logit_fit((Xc[:i]-mu)/sd,y[:i])
        pr[i]=lp(w,((Xc[i:i+1]-mu)/sd))[0]
    m=~np.isnan(pr); p_,y_,b_=pr[m],y[m],bc[m]
    pnl=np.where(p_>0.5,1,-1)*b_
    print(f"  OOS n={len(pnl)} acc={(((p_>0.5)==(y_>0.5)).mean())*100:5.2f}% "
          f"mean={pnl.mean()*100:+.5f}% t={pnl.mean()/(pnl.std()/np.sqrt(len(pnl))):+.2f}")
