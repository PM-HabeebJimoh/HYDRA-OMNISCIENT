"""Aggressive hunt for >80% accuracy.
Every 3-pair alignment triplet x every target pair x strength filters,
on 2026 daily. Then the same on 4H/1H for the core 3. Report anything >=80%
and immediately test it against the best-of-N selection-noise null."""
import json,itertools,math
import numpy as np
R=np.load('/tmp/R2026.npy'); meta=json.load(open('/tmp/R2026meta.json'))
SYMS=meta['syms']; n,m=R.shape
S=np.sign(R)

def wilson(k,nn):
    p=k/nn; z=1.96; den=1+z*z/nn
    c=(p+z*z/(2*nn))/den; h=z*math.sqrt(p*(1-p)/nn+z*z/(4*nn*nn))/den
    return c-h,c+h

MINN=20
found=[]; tested=0
for trip in itertools.combinations(range(m),3):
    al=S[:,list(trip)].sum(1); fire=np.abs(al)==3
    strength=np.abs(R[:,list(trip)]).mean(1)
    for th in (0.0,0.002,0.004,0.006):
        f=fire&(strength>=th)
        if f[:-1].sum()<MINN: continue
        for j in range(m):
            nxt=S[1:,j]
            for mode in (1,-1):
                sig=np.sign(al[:-1])*mode
                mask=f[:-1]&(nxt!=0)
                nn=int(mask.sum())
                if nn<MINN: continue
                k=int((sig[mask]==nxt[mask]).sum()); acc=k/nn; tested+=1
                if acc>=0.70: found.append((acc,nn,k,trip,th,j,mode))
found.sort(reverse=True)
print(f"DAILY 2026: tested {tested:,} pair/triplet/filter/direction combinations")
print(f"combos reaching >=70%: {len(found)}   >=80%: {sum(1 for f in found if f[0]>=0.80)}\n")
print(f"{'acc%':>7} {'n':>4} {'95% CI':>15} {'target':>8} {'dir':>7} {'minstr':>7}  alignment triplet")
for acc,nn,k,trip,th,j,mode in found[:20]:
    lo,hi=wilson(k,nn)
    print(f"{acc*100:7.2f} {nn:4d} [{lo*100:5.1f},{hi*100:5.1f}] {SYMS[j]:>8} {'follow' if mode>0 else 'fade':>7} {th*100:6.2f}%  {'+'.join(SYMS[t] for t in trip)}")

if found:
    best=found[0]
    print(f"\n--- selection-noise null for the {best[0]*100:.1f}% winner ---")
    rng=np.random.default_rng(9); mx=[]
    for _ in range(200):
        flip=rng.choice([-1,1],size=(n,1)); Rp=R*flip; Sp=np.sign(Rp)
        b=0
        for trip in itertools.combinations(range(m),3):
            al=Sp[:,list(trip)].sum(1); fire=np.abs(al)==3
            st=np.abs(Rp[:,list(trip)]).mean(1)
            for th in (0.0,0.002,0.004,0.006):
                f=fire&(st>=th)
                if f[:-1].sum()<MINN: continue
                for j in range(m):
                    nxt=Sp[1:,j]; mask=f[:-1]&(nxt!=0); nn=int(mask.sum())
                    if nn<MINN: continue
                    a=np.sign(al[:-1])
                    kk=max(int((a[mask]==nxt[mask]).sum()),int((-a[mask]==nxt[mask]).sum()))
                    b=max(b,kk/nn)
        mx.append(b)
    mx=np.array(mx)
    print(f"  best accuracy from PURE NOISE, same search: median {np.median(mx)*100:.1f}%  95th {np.percentile(mx,95)*100:.1f}%  max {mx.max()*100:.1f}%")
    print(f"  our best {best[0]*100:.1f}%  -> p = {(mx>=best[0]).mean():.3f}")
    print(f"  verdict: {'REAL' if (mx>=best[0]).mean()<0.05 else 'INDISTINGUISHABLE FROM NOISE'}")
