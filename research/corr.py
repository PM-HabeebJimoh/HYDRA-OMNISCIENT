import numpy as np
from research.data import panels
P=panels()
for tf in ('D1','H4','H1'):
    d=P[tf]; r=(d['C']-d['O'])/d['O']
    c=np.corrcoef(r.T)
    print(f"--- {tf} correlation of open->close returns ---")
    print("        gold     eur     aud")
    for i,a in enumerate(('gold','eur','aud')):
        print(f"  {a:5s} "+" ".join(f"{c[i,j]:7.3f}" for j in range(3)))
    # effective number of independent bets
    w=np.ones(3)/3; sd=r.std(0)
    port=(r*w).sum(1).std(); naive=np.sqrt(((w*sd)**2).sum())
    print(f"  basket sd {port*100:.4f}%  vs zero-corr sd {naive*100:.4f}%  -> N_eff = {(naive/port)**2:.2f} independent bets")
    # how often do all 3 agree
    s=np.sign(r); agree=(np.abs(s.sum(1))==3).mean()
    print(f"  all-3-agree fires on {agree*100:.1f}% of bars")
    print()
print("PHYSICS: the 3 legs are one USD bet. N_eff ~1.5, not 3.")
print("Sharpe scales sqrt(N_eff). To lift portfolio Sharpe you need UNCORRELATED streams,")
print("not more leverage on the same stream.")
