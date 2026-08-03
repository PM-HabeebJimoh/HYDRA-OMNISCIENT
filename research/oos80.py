"""The honest test: pick the best >=80% combos on the FIRST half of 2026,
then trade them UNSEEN on the second half. A real edge persists; noise does not."""
import json,itertools,math
import numpy as np
R=np.load('/tmp/R2026.npy'); meta=json.load(open('/tmp/R2026meta.json'))
SYMS=meta['syms']; dates=meta['dates']; n,m=R.shape
S=np.sign(R)
split=n//2
print(f"TRAIN {dates[0]} -> {dates[split-1]} ({split} bars)")
print(f"TEST  {dates[split]} -> {dates[-1]} ({n-split} bars)\n")

def acc_on(lo,hi,trip,th,j,mode,minn):
    al=S[:,list(trip)].sum(1); fire=np.abs(al)==3
    st=np.abs(R[:,list(trip)]).mean(1)
    f=fire&(st>=th)
    idx=np.arange(n-1)
    sel=(idx>=lo)&(idx<hi)&f[:-1]&(S[1:,j]!=0)
    nn=int(sel.sum())
    if nn<minn: return None,nn
    sig=np.sign(al[:-1])*mode
    return float((sig[sel]==S[1:,j][sel]).mean()),nn

# select on TRAIN
cands=[]
for trip in itertools.combinations(range(m),3):
    for th in (0.0,0.002,0.004,0.006):
        for j in range(m):
            for mode in (1,-1):
                a,nn=acc_on(0,split,trip,th,j,mode,10)
                if a is not None and a>=0.80: cands.append((a,nn,trip,th,j,mode))
cands.sort(reverse=True)
print(f"combos >=80% on TRAIN half: {len(cands)}")
print(f"\n{'TRAIN acc':>10} {'n':>4} | {'TEST acc':>9} {'n':>4} | {'target':>8} {'dir':>7} {'triplet'}")
te=[]
for a,nn,trip,th,j,mode in cands[:20]:
    b,mn=acc_on(split,n,trip,th,j,mode,5)
    if b is None:
        print(f"{a*100:9.1f}% {nn:4d} |    (n<5) {mn:4d} | {SYMS[j]:>8} {'foll' if mode>0 else 'fade':>7} {'+'.join(SYMS[t] for t in trip)}")
        continue
    te.append(b)
    print(f"{a*100:9.1f}% {nn:4d} | {b*100:8.1f}% {mn:4d} | {SYMS[j]:>8} {'foll' if mode>0 else 'fade':>7} {'+'.join(SYMS[t] for t in trip)}")
if te:
    print(f"\nMean TRAIN accuracy of selected combos: {np.mean([c[0] for c in cands[:20]])*100:.1f}%")
    print(f"Mean TEST  accuracy of the SAME combos: {np.mean(te)*100:.1f}%")
    print(f"Combos still >=80% out-of-sample: {sum(1 for b in te if b>=0.80)}/{len(te)}")
    print(f"Combos better than coin-flip OOS:  {sum(1 for b in te if b>0.50)}/{len(te)}")
