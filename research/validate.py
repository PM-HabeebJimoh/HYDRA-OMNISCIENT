"""Take the grid's top candidates and stress them:
   (a) first-half vs second-half split, (b) month-by-month stability, (c) inverse check."""
import numpy as np, math
from research.data import panels,utc
P=panels()

def trades(d,follow,H,stop,minstr,subset,lo=None,hi=None):
    O,Hi,Lo,C=d['O'],d['H'],d['L'],d['C']; ts=d['ts']; idx=list(subset)
    r=(C-O)/O; sub=r[:,idx]; n=len(r); T=[];TS=[]
    for i in range(n-H-1):
        s=np.sign(sub[i])
        if abs(s.sum())!=len(idx): continue
        if np.abs(sub[i]).mean()<minstr: continue
        dirn=int(s[0])*(1 if follow else -1); j=i+1
        if lo is not None and not (lo<=ts[j]<hi): continue
        legs=[]
        for a in idx:
            ep=O[j,a]; ex=C[min(j+H-1,n-1),a]
            for m in range(j,min(j+H,n)):
                if stop:
                    if dirn>0 and Lo[m,a]<=ep*(1-stop): ex=ep*(1-stop);break
                    if dirn<0 and Hi[m,a]>=ep*(1+stop): ex=ep*(1+stop);break
            legs.append(dirn*(ex-ep)/ep)
        T.append(np.mean(legs)); TS.append(ts[j])
    return np.array(T),np.array(TS)

def stat(a):
    if len(a)<5: return (len(a),float('nan'),float('nan'))
    return len(a),a.mean()*100,a.mean()/(a.std()/np.sqrt(len(a)))

CANDS=[("D1 fadeA",   'D1',False,3,0.002,0.003,(2,)),
       ("D1 follA",   'D1',True, 3,0.002,0.003,(2,)),
       ("H4 follG",   'H4',True, 5,0.010,0.003,(0,)),
       ("H4 follG.1", 'H4',True, 5,0.010,0.001,(0,)),
       ("H1 fadeEA",  'H1',False,3,0.000,0.000,(1,2)),
      ]
print("IN/OUT SPLIT (chronological halves)")
print(f"{'name':>10} {'n':>5} {'full t':>7} | {'n1':>4} {'t1':>7} | {'n2':>4} {'t2':>7}")
for nm,tf,f,H,st,ms,sub in CANDS:
    d=P[tf]; T,TS=trades(d,f,H,st,ms,sub)
    mid=TS[len(TS)//2]
    A=T[TS<mid]; B=T[TS>=mid]
    n,m,t=stat(T); n1,m1,t1=stat(A); n2,m2,t2=stat(B)
    print(f"{nm:>10} {n:5d} {t:+7.2f} | {n1:4d} {t1:+7.2f} | {n2:4d} {t2:+7.2f}")

print("\nMONTH-BY-MONTH mean% (the strategy must be consistent, not one lucky month)")
months=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
for nm,tf,f,H,st,ms,sub in CANDS:
    d=P[tf]; T,TS=trades(d,f,H,st,ms,sub)
    lab=[utc(x).strftime('%Y-%m') for x in TS]
    row=[]
    for mo in months:
        v=T[np.array([l==mo for l in lab])]
        row.append(f"{v.mean()*100:+7.3f}" if len(v)>=3 else "      .")
    print(f"{nm:>10} "+" ".join(row))
