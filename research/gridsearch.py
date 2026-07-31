"""Exhaustive search over the Agba-Metta rule FAMILY, leak-free.
Signal bar closes -> enter next bar open -> exit after H bars or stop.
Grid: direction(follow/fade) x holding x stop x strength filter x asset subset x session.
Report best by t-stat, then correct for multiple testing."""
import numpy as np, itertools, math
from research.data import panels,utc
P=panels()

def run(d,follow,H,stop,minstr,subset,hours=None):
    O,Hi,Lo,C=d['O'],d['H'],d['L'],d['C']; ts=d['ts']
    r=(C-O)/O; idx=list(subset)
    sub=r[:,idx]
    n=len(r); out=[]
    for i in range(n-H-1):
        s=np.sign(sub[i])
        if not (np.abs(s.sum())==len(idx)): continue
        strength=np.abs(sub[i]).mean()
        if strength<minstr: continue
        dirn=int(s[0])*(1 if follow else -1)
        j=i+1
        if hours is not None and utc(ts[j]).hour not in hours: continue
        e=O[j,idx]
        # exit after H bars (close of bar j+H-1) or stop
        legs=[]
        for kk,a in enumerate(idx):
            ep=O[j,a]; sl=ep*(1-stop*dirn) if stop else None
            ex=C[min(j+H-1,n-1),a]; hit=False
            for m in range(j,min(j+H,n)):
                if stop:
                    if dirn>0 and Lo[m,a]<=ep*(1-stop): ex=ep*(1-stop);hit=True;break
                    if dirn<0 and Hi[m,a]>=ep*(1+stop): ex=ep*(1+stop);hit=True;break
            legs.append(dirn*(ex-ep)/ep)
        out.append(np.mean(legs))
    a=np.array(out)
    if len(a)<15: return None
    return len(a),a.mean(),a.mean()/(a.std()/np.sqrt(len(a)))

SUBS=[(0,1,2),(0,1),(0,2),(1,2),(0,),(1,),(2,)]
res=[]
for tf in ('D1','H4','H1'):
    d=P[tf]
    for follow in (True,False):
        for Hh in (1,2,3,5):
            for stop in (0.0,0.002,0.005,0.01):
                for minstr in (0.0,0.001,0.003):
                    for sub in SUBS:
                        o=run(d,follow,Hh,stop,minstr,sub)
                        if o: res.append((abs(o[2]),tf,follow,Hh,stop,minstr,sub,o))
res.sort(reverse=True)
print(f"TOTAL CONFIGS TESTED: {len(res)}")
print(f"{'tf':>3} {'dir':>6} {'H':>2} {'stop':>6} {'minstr':>7} {'assets':>9} {'n':>5} {'mean%':>9} {'t':>7}")
for k in res[:15]:
    _,tf,f,Hh,st,ms,sub,(n,m,t)=k
    nm=''.join('GEA'[i] for i in sub)
    print(f"{tf:>3} {'follow' if f else 'fade':>6} {Hh:2d} {st*100:5.2f}% {ms*100:6.3f}% {nm:>9} {n:5d} {m*100:+9.4f} {t:+7.2f}")
best=res[0][0]; M=len(res)
# Bonferroni + expected max |t| under null
from math import erf,sqrt
p=2*(1-0.5*(1+erf(best/sqrt(2))))
print(f"\nBest |t| = {best:.2f}, raw p = {p:.4f}")
print(f"Bonferroni threshold over {M} tests: p < {0.05/M:.2e}  -> {'SURVIVES' if p<0.05/M else 'FAILS'}")
exp_max=sqrt(2*math.log(M))
print(f"Expected max |t| from PURE NOISE over {M} independent tests ~ {exp_max:.2f}")
print("=> observed best is",'ABOVE' if best>exp_max else 'BELOW',"the noise expectation.")
