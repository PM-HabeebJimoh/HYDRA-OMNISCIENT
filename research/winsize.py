"""Why 57.94% accuracy earns nothing: check win/loss SIZE asymmetry.
Accuracy is not edge. This is the trap in judging signals by hit-rate."""
import json
import numpy as np
D=json.load(open('/tmp/allpairs.json'))
CORE=('XAUUSD','EURUSD','AUDUSD')
ds=sorted(d for d in D if all(s in D[d] for s in CORE))
r={s:np.array([(D[d][s]['c']-D[d][s]['o'])/D[d][s]['o'] for d in ds]) for s in CORE}
S=np.array([np.sign(r[s]) for s in CORE]); al=np.sign(S.sum(0)); fire=np.abs(S.sum(0))==3

print(f"{'pair':>8} {'signal':>16} {'n':>4} {'acc%':>6} {'avgWin%':>8} {'avgLoss%':>9} {'edge%/trade':>12} {'t':>6}")
for sym in CORE:
    g=r[sym]; nx=np.sign(g[1:]); m=fire[:-1]&(nx!=0)
    for mode,lab in ((-1,'AM-align FADE'),(1,'AM-align FOLLOW')):
        sig=al[:-1]*mode
        win=sig[m]==nx[m]
        pnl=np.where(win,np.abs(g[1:][m]),-np.abs(g[1:][m]))
        w=pnl[pnl>0]; l=pnl[pnl<0]
        t=pnl.mean()/(pnl.std()/np.sqrt(len(pnl)))
        print(f"{sym:>8} {lab:>16} {len(pnl):4d} {win.mean()*100:6.2f} {w.mean()*100:8.4f} {l.mean()*100:9.4f} {pnl.mean()*100:+12.4f} {t:+6.2f}")

print("\nXAUUSD AM-align FADE, dissected:")
g=r['XAUUSD']; nx=np.sign(g[1:]); m=fire[:-1]&(nx!=0)
sig=-al[:-1]; win=sig[m]==nx[m]; mv=np.abs(g[1:][m])
print(f"  when RIGHT ({win.sum()} trades): average gold move captured = {mv[win].mean()*100:.4f}%")
print(f"  when WRONG ({(~win).sum()} trades): average gold move lost   = {mv[~win].mean()*100:.4f}%")
print(f"  -> losses are {mv[~win].mean()/mv[win].mean():.2f}x bigger than wins")
print(f"  net {mv[win].sum()*100:.2f}% won - {mv[~win].sum()*100:.2f}% lost = {(mv[win].sum()-mv[~win].sum())*100:+.2f}% total")
print(f"\n  BREAK-EVEN accuracy needed given this payoff ratio: "
      f"{mv[~win].mean()/(mv[win].mean()+mv[~win].mean())*100:.1f}%")
print(f"  actual accuracy: {win.mean()*100:.1f}%  -> margin only {win.mean()*100-mv[~win].mean()/(mv[win].mean()+mv[~win].mean())*100:+.1f} points")
