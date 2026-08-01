#!/usr/bin/env python3
"""THE ANTICIPATORY MODEL.

I can predict NEXT-BAR RANGE with OOS R2 32% (1H), 23% (4H).
That is a FORECAST of what is about to happen - not a reaction.

Convert forecast -> trade:
  forecast says BIG range  -> place a bracket (profit from the move, either way)
  forecast says SMALL range-> stand aside (whipsaw risk, no move to capture)

This is the model KNOWING BEFORE IT HAPPENS. Test it honestly."""
import sys, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h(); p4=resample_4h(p1)
def build(P):
    ks=sorted(P); X=[]; T=[]
    for i in range(22,len(ks)-1):
        b=P[ks[i]]; pv=P[ks[i-1]]
        row=[]
        for a in A:
            o,h,l,c=b[a]['open'],b[a]['high'],b[a]['low'],b[a]['close']
            rng=max(h-l,1e-12)
            row += [(c-o)/o,(h-max(o,c))/o,(min(o,c)-l)/o,((c-l)-(h-c))/rng,
                    abs(c-o)/rng,(o-pv[a]['close'])/pv[a]['close'],
                    ((h-max(o,c))-(min(o,c)-l))/rng, rng/o]
        for a in A:
            past=[(P[ks[j]][a]['high']-P[ks[j]][a]['low'])/P[ks[j]][a]['open'] for j in range(i-20,i)]
            row.append(np.mean(past)); row.append(np.std(past))
        clv=[((b[a]['close']-b[a]['low'])-(b[a]['high']-b[a]['close']))/max(b[a]['high']-b[a]['low'],1e-12) for a in A]
        row += [np.mean(clv),np.std(clv)]
        X.append(row); T.append(i)
    return np.array(X),np.array(T),ks
def yrange(P,ks,T):
    return np.array([np.mean([(P[ks[i+1]][a]['high']-P[ks[i+1]][a]['low'])/P[ks[i+1]][a]['open'] for a in A]) for i in T])
def wf(X,y,l2=10.0,frac=0.4):
    n=len(y); s=int(n*frac); pred=np.full(n,np.nan)
    for i in range(s,n):
        Xt,yt=X[:i],y[:i]; mu,sd=Xt.mean(0),Xt.std(0)+1e-12
        Z=(Xt-mu)/sd; Zb=np.column_stack([np.ones(len(Z)),Z])
        Aa=Zb.T@Zb+l2*np.eye(Zb.shape[1]); Aa[0,0]-=l2
        try: w=np.linalg.solve(Aa,Zb.T@yt)
        except Exception: continue
        pred[i]=np.r_[1,(X[i]-mu)/sd]@w
    return pred
def trade(P,ks,T,pred,thresh_q,w=1.0,hold=3):
    """Only trade when the FORECAST says range will be large."""
    m=~np.isnan(pred)
    if m.sum()<50: return None
    th=np.quantile(pred[m],thresh_q)
    ev=[]
    for idx in np.where(m)[0]:
        if pred[idx]<th: continue
        i=T[idx]
        if i+1+hold>=len(ks): continue
        for a in A:
            past=[(P[ks[j]][a]['high']-P[ks[j]][a]['low'])/P[ks[j]][a]['open'] for j in range(i-20,i)]
            av=np.mean(past)
            o=P[ks[i+1]][a]['open']; up=o*(1+w*av); dn=o*(1-w*av); side=0; ent=None
            for j in range(i+1,min(i+1+hold,len(ks))):
                bb=P[ks[j]][a]; hu=bb['high']>=up; hd=bb['low']<=dn
                if hu and hd: ev.append((ks[i],-2*w*av-2*COST[a])); side=-99; break
                if hu: side=1; ent=up; break
                if hd: side=-1; ent=dn; break
            if side in (0,-99): continue
            ex=P[ks[min(i+hold,len(ks)-1)]][a]['close']
            ev.append((ks[i],((ex-ent)/ent if side>0 else (ent-ex)/ent)-2*COST[a]))
    return ev
print("="*100)
print("ANTICIPATORY MODEL — trade only when the forecast predicts a BIG move")
print("="*100)
for tf,P in (('4H',p4),('1H',p1)):
    X,T,ks=build(P); y=yrange(P,ks,T); pred=wf(X,y)
    m=~np.isnan(pred)
    ic=np.corrcoef(pred[m],y[m])[0,1]
    print(f"\n--- {tf} --- forecast OOS IC={ic:+.4f} (R2 {ic**2*100:.1f}%)")
    print(f"  {'forecast filter':>22} {'n':>6} {'WR':>7} {'mean':>10} {'t':>7}")
    for q,lab in ((0.0,'all bars (no filter)'),(0.5,'top 50% forecast'),
                  (0.7,'top 30% forecast'),(0.85,'top 15% forecast'),(0.95,'top 5% forecast')):
        ev=trade(P,ks,T,pred,q)
        if not ev or len(ev)<40: continue
        g=np.array([e[1] for e in ev])
        t=g.mean()/(g.std()/np.sqrt(len(g)))
        print(f"  {lab:>22} {len(g):6d} {(g>0).mean()*100:6.2f}% {g.mean()*100:+9.4f}% {t:+7.2f}")
