"""Perfect-foresight ceiling and honest edge measurement on REAL bars."""
import numpy as np, math
from research.data import panels,utc
P=panels()
np.set_printoptions(suppress=True)

for tf in ('D1','H4','H1'):
    d=P[tf]; O,H,L,C=d['O'],d['H'],d['L'],d['C']
    r=(C-O)/O                     # open->close return per bar per asset
    print(f"--- {tf}  bars={len(r)} ---")
    print(f"  per-asset |o->c| mean: gold {np.abs(r[:,0]).mean()*100:.4f}%  eur {np.abs(r[:,1]).mean()*100:.4f}%  aud {np.abs(r[:,2]).mean()*100:.4f}%")
    bask=r.mean(1)
    print(f"  basket o->c  sd {bask.std()*100:.4f}%   mean|.| {np.abs(bask).mean()*100:.4f}%")
    # perfect foresight: know sign of basket each bar
    pf=np.abs(bask)
    print(f"  PERFECT-SIGN basket edge/bar = {pf.mean()*100:.4f}%  (SR/bar = {pf.mean()/pf.std():.3f})")
    # random sign
    print(f"  actual mean basket = {bask.mean()*100:+.4f}%  SR/bar {bask.mean()/bask.std():+.4f}")
    # how much of a Sharpe does a q-accurate directional forecast give?
    print("   directional accuracy -> per-bar SR of a sign-following strategy:")
    for acc in (0.52,0.55,0.60,0.65,0.70):
        mu=(2*acc-1)*np.abs(bask).mean()
        sd=bask.std()
        print(f"     acc {acc:.2f} -> mu {mu*100:.4f}%  SR/bar {mu/sd:.3f}  annSR {mu/sd*math.sqrt(len(r)/(202/252)):.2f}")
    print()
