"""
VERIFY THE 86.8%.

1H range, top-5% confidence, walk-forward ridge -> 86.8% accuracy.
That clears the 85% target. Before claiming it, every audit that killed
the previous nine results.

The specific ways this could be fake:
  A. BASE RATE. Is "range > trailing median" actually 50/50, or is the
     top-confidence subset just picking a lopsided sub-population?
  B. LOOK-AHEAD. Is the trailing median computed with future data?
  C. TRIVIALITY. Is it just "volatility clusters" restated? A one-feature
     benchmark must be beaten.
  D. STABILITY. Split-half, month-by-month.
  E. SAMPLE. n at top-5% of 3793 is ~190. Enough?
  F. USEFULNESS. Does an 86.8% range call convert to money?
"""
import json, glob, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

raw = {}
for f in sorted(glob.glob(str(ROOT/'data/raw/intraday/XAUUSD*.json'))):
    d = json.load(open(f))
    for i, t in enumerate(d['t']):
        raw[t] = (d['o'][i], d['h'][i], d['l'][i], d['c'][i])
T = sorted(raw); B = [raw[t] for t in T]
say(f"1H bars: {len(B)}")

X, Y, R, TS = [], [], [], []
for i in range(25, len(B)-1):
    o, h, l, c = B[i]
    rr = [(B[j][1]-B[j][2])/B[j][0] for j in range(i-20, i+1)]
    r  = [(B[j][3]-B[j][0])/B[j][0] for j in range(i-20, i+1)]
    rng = max(h-l, 1e-12)
    atr, atr5, atr3 = np.mean(rr), np.mean(rr[-5:]), np.mean(rr[-3:])
    X.append([rr[-1], atr3, atr5, atr, np.std(rr[-10:]),
              atr3/(atr+1e-12), atr5/(atr+1e-12),
              abs(c-o)/rng, (h-max(o,c))/rng, (min(o,c)-l)/rng,
              np.std(r[-10:]), np.mean(np.abs(r[-5:])),
              float(dt.datetime.utcfromtimestamp(T[i]).hour),
              float(dt.datetime.utcfromtimestamp(T[i]).weekday())])
    nx = B[i+1]
    Y.append((nx[1]-nx[2])/nx[0])
    R.append(float(np.median(rr)))      # trailing median, causal
    TS.append(T[i])
X, Y, R, TS = np.array(X), np.array(Y), np.array(R), np.array(TS)
LAB = (Y > R).astype(int)

say()
say("="*76)
say("A. BASE RATE -- is the question genuinely 50/50?")
say("="*76)
say(f"  overall P(range > trailing median) = {LAB.mean()*100:.2f}%")
say(f"  majority-class baseline            = {max(LAB.mean(),1-LAB.mean())*100:.2f}%")

def wf(X, lab, ridge=10.0, start=80):
    pred, act, idx = [], [], []
    for i in range(start, len(X)):
        Xt = X[:i]; Yt = lab[:i].astype(float)
        mu, sd = Xt.mean(0), Xt.std(0)+1e-12
        Z = (Xt-mu)/sd
        A = Z.T@Z + ridge*np.eye(Z.shape[1])
        w = np.linalg.solve(A, Z.T@(Yt-Yt.mean()))
        pred.append(float(((X[i]-mu)/sd)@w + Yt.mean()))
        act.append(lab[i]); idx.append(i)
    return np.array(pred), np.array(act), np.array(idx)

pred, act, idx = wf(X, LAB)
conf = np.abs(pred-0.5)
say()
say("="*76)
say("B. THE CONFIDENCE LADDER (reproduce)")
say("="*76)
for q in (0.0, .5, .8, .9, .95, .98):
    m = conf >= np.quantile(conf, q)
    if m.sum() < 10: continue
    a = np.mean((pred[m] > .5).astype(int) == act[m])*100
    base = max(act[m].mean(), 1-act[m].mean())*100
    say(f"  top {int((1-q)*100):>3d}%  n={m.sum():5d}  acc {a:5.2f}%   "
        f"(majority class in subset {base:5.2f}%)  lift {a-base:+5.2f}")

say()
say("="*76)
say("C. TRIVIALITY -- beat the one-feature benchmark")
say("="*76)
say("  Simplest possible rule: 'next range beats median if CURRENT range does'")
naive = (X[:, 0] > R).astype(int)[idx]
a_naive = np.mean(naive == act)*100
say(f"  naive persistence accuracy: {a_naive:.2f}%")
p1, a1, i1 = wf(X[:, [0]], LAB)
say(f"  ridge on last-range only  : {np.mean((p1>.5).astype(int)==a1)*100:.2f}%")
say(f"  full 14-feature model     : {np.mean((pred>.5).astype(int)==act)*100:.2f}%")
c1 = np.abs(p1-0.5)
m1 = c1 >= np.quantile(c1, .95)
say(f"  one-feature top-5%        : "
    f"{np.mean((p1[m1]>.5).astype(int)==a1[m1])*100:.2f}%")
m = conf >= np.quantile(conf, .95)
say(f"  14-feature  top-5%        : "
    f"{np.mean((pred[m]>.5).astype(int)==act[m])*100:.2f}%")

say()
say("="*76)
say("D. STABILITY")
say("="*76)
h = len(pred)//2
for lab, s in [('first half ', slice(0, h)), ('second half', slice(h, None))]:
    pp, aa, cc = pred[s], act[s], conf[s]
    mm = cc >= np.quantile(cc, .95)
    say(f"  {lab}  all {np.mean((pp>.5).astype(int)==aa)*100:5.2f}%   "
        f"top5% {np.mean((pp[mm]>.5).astype(int)==aa[mm])*100:5.2f}%  n={mm.sum()}")
say()
bym = collections.defaultdict(list)
m = conf >= np.quantile(conf, .95)
for k, i in enumerate(idx):
    if m[k]:
        bym[dt.datetime.utcfromtimestamp(TS[i]).strftime('%Y-%m')].append(
            int((pred[k] > .5) == act[k]))
say("  month by month, top-5% confidence:")
for k in sorted(bym):
    v = bym[k]
    say(f"    {k}  n={len(v):3d}  acc {np.mean(v)*100:5.1f}%")
say(f"  months at or above 85%: "
    f"{sum(1 for v in bym.values() if np.mean(v)>=0.85)}/{len(bym)}")

say()
say("="*76)
say("E. SIGN-FLIP NULL ON THE TOP-5% CELL")
say("="*76)
m = conf >= np.quantile(conf, .95)
hits = ((pred[m] > .5).astype(int) == act[m]).astype(float)
n = len(hits); a = hits.mean()
z = (a-0.5)/np.sqrt(0.25/n)
say(f"  n={n}  acc {a*100:.2f}%  z vs 50% = {z:+.2f}")
say(f"  (this is ONE pre-specified cell, not a search)")

say()
say("="*76)
say("F. DOES IT CONVERT TO MONEY?")
say("="*76)
say("  Knowing the range will be LARGE -> buy a straddle sized to the")
say("  trailing median, so the forecast and the hurdle do NOT scale together.")
SPREAD = 0.00012
for q in (0.0, .8, .9, .95):
    m = conf >= np.quantile(conf, q)
    pnl = []
    for k, i in enumerate(idx):
        if not m[k] or pred[k] <= .5: continue
        w = R[i]                      # band = trailing median, NOT forecast
        o, hh, ll, cc2 = B[i+1]
        up, dn = o*(1+w/2), o*(1-w/2)
        hu, hd = hh >= up, ll <= dn
        if hu and hd:  v = -w - 2*SPREAD
        elif hu:       v = (cc2-up)/o - SPREAD
        elif hd:       v = (dn-cc2)/o - SPREAD
        else:          continue
        pnl.append(v)
    if len(pnl) < 20: continue
    mm2, tt, nn = tstat(pnl)
    say(f"  top {int((1-q)*100):>3d}% n={nn:5d}  mean {mm2*100:+.4f}%  "
        f"t={tt:+6.2f}  WR {np.mean([x>0 for x in pnl])*100:.1f}%")
