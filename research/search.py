"""Wide, leak-free model search. Many causal features x several model classes.
Reports OOS directional accuracy and t-stat. Includes a shuffled-label control."""
import numpy as np, itertools
from research.data import panels
P=panels()

def build(d):
    O,H,L,C=d['O'],d['H'],d['L'],d['C']
    r=(C-O)/O; b=r.mean(1); n=len(b)
    tr=(H-L)/O
    body=np.abs(C-O)/O
    uw=(H-np.maximum(O,C))/O; lw=(np.minimum(O,C)-L)/O
    def lag(x,k):
        y=np.full(n,np.nan)
        if k<len(x): y[k:]=x[:-k] if x.ndim==1 else x[:-k]
        return y
    def roll(x,w,f):
        y=np.full(n,np.nan)
        for i in range(w+1,n):
            seg=x[i-w:i]
            if not np.isnan(seg).any(): y[i]=f(seg)
        return y
    F={}
    for k in (1,2,3,4,5): F[f'b{k}']=lag(b,k)
    for w in (3,5,10,20,50): F[f'bma{w}']=roll(b,w,np.mean)
    for w in (5,10,20,50): F[f'vol{w}']=roll(b,w,np.std)
    for j,a in enumerate(('gold','eur','aud')):
        for k in (1,2,3): F[f'r{k}_{a}']=lag(r[:,j],k)
        F[f'mom10_{a}']=roll(r[:,j],10,np.mean)
        F[f'atr14_{a}']=roll(tr[:,j],14,np.mean)
        F[f'uw1_{a}']=lag(uw[:,j],1); F[f'lw1_{a}']=lag(lw[:,j],1)
    F['tr1']=lag(tr.mean(1),1); F['body1']=lag(body.mean(1),1)
    F['align1']=lag(np.sign(r).sum(1),1); F['align2']=lag(np.sign(r).sum(1),2)
    F['disp1']=lag(r.std(1),1)
    gap=np.full(n,np.nan); gap[1:]=((O[1:]-C[:-1])/C[:-1]).mean(1); F['gap']=gap
    for w in (5,20): F[f'zb{w}']=(F['b1']-F[f'bma{w}'])/(F[f'vol{w}']+1e-9)
    F['rsi14']=roll(b,14,lambda s:(s[s>0].sum()/(np.abs(s).sum()+1e-12)))
    names=list(F)
    return np.column_stack([F[k] for k in names]),b,names

def ridge(X,y,l2):
    Xb=np.column_stack([np.ones(len(X)),X])
    A=Xb.T@Xb+l2*np.eye(Xb.shape[1]); A[0,0]-=l2
    return np.linalg.solve(A,Xb.T@y)
def rpred(w,X): return np.column_stack([np.ones(len(X)),X])@w

def logit(X,y,l2,iters=150):
    Xb=np.column_stack([np.ones(len(X)),X]); w=np.zeros(Xb.shape[1])
    for _ in range(iters):
        p=1/(1+np.exp(-np.clip(Xb@w,-30,30))); g=Xb.T@(p-y)+l2*np.r_[0,w[1:]]
        Hs=Xb.T@(Xb*(p*(1-p))[:,None])+l2*np.eye(Xb.shape[1])
        try: st=np.linalg.solve(Hs,g)
        except np.linalg.LinAlgError: break
        w-=st
        if np.abs(st).max()<1e-9: break
    return w
def lpred(w,X): return 1/(1+np.exp(-np.clip(np.column_stack([np.ones(len(X)),X])@w,-30,30)))-0.5

def wf(Xc,bc,kind,l2,shuffle=False,seed=0):
    n=len(bc); start=max(60,int(n*0.4)); s=np.full(n,np.nan)
    y=bc.copy()
    if shuffle:
        rng=np.random.default_rng(seed); y=bc[rng.permutation(n)]
    for i in range(start,n):
        mu,sd=Xc[:i].mean(0),Xc[:i].std(0)+1e-12; Z=(Xc[:i]-mu)/sd
        zi=(Xc[i:i+1]-mu)/sd
        if kind=='ridge': s[i]=rpred(ridge(Z,y[:i],l2),zi)[0]
        else: s[i]=lpred(logit(Z,(y[:i]>0).astype(float),l2),zi)[0]
    m=~np.isnan(s)
    pnl=np.sign(s[m])*bc[m]
    return len(pnl),(np.sign(s[m])==np.sign(bc[m])).mean(),pnl.mean(),pnl.mean()/(pnl.std()/np.sqrt(len(pnl)))

print(f"{'tf':>3} {'model':>6} {'l2':>7} {'n':>5} {'acc%':>7} {'mean%':>9} {'t':>7}   {'shuf t':>7}")
for tf in ('D1','H4','H1'):
    d=P[tf]; X,b,names=build(d)
    ok=~np.isnan(X).any(1); Xc,bc=X[ok],b[ok]
    for kind in ('ridge','logit'):
        for l2 in (1.0,10.0,100.0,1000.0):
            n,a,m,t=wf(Xc,bc,kind,l2)
            _,_,_,ts=wf(Xc,bc,kind,l2,shuffle=True,seed=11)
            print(f"{tf:>3} {kind:>6} {l2:7.0f} {n:5d} {a*100:7.2f} {m*100:+9.5f} {t:+7.2f}   {ts:+7.2f}")
