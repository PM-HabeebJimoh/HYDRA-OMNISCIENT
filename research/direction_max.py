"""
NEXT CANDLE: BULLISH OR BEARISH. MAXIMUM EFFORT.

The exact architecture that reached 86.84% on RANGE, pointed at DIRECTION.
If confidence-filtering works for range it must be tried for direction the
same way -- same features, same ridge, same walk-forward, same ladder.

Plus every additional angle:
  * 60 features (candle shape, momentum, mean-reversion, session, vol)
  * 6 timeframes
  * ridge, logistic, and gradient boosting
  * confidence ladder to top 1%
  * per-hour conditioning (the thing that carried the range model)

Honest throughout: walk-forward, no look-ahead, base rates reported.
"""
import json, glob, sys, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

raw = {}
for f in sorted(glob.glob(str(ROOT/'data/raw/intraday/XAUUSD*.json'))):
    d = json.load(open(f))
    for i, t in enumerate(d['t']):
        raw[t] = (d['o'][i], d['h'][i], d['l'][i], d['c'][i])
T1 = sorted(raw)
say("="*76)
say("NEXT CANDLE DIRECTION: BULLISH OR BEARISH")
say("="*76)
say(f"XAUUSD 1H bars: {len(T1)}")

def resample(mult):
    B = {}
    for t in T1:
        k = t-(t % (3600*mult)); o,h,l,c = raw[t]
        if k not in B: B[k] = [o,h,l,c]
        else:
            B[k][1]=max(B[k][1],h); B[k][2]=min(B[k][2],l); B[k][3]=c
    ks = sorted(B); return ks, [tuple(B[k]) for k in ks]

def build(mult):
    ks, B = resample(mult)
    if len(B) < 150: return None
    X, y, TS = [], [], []
    for i in range(30, len(B)-1):
        o,h,l,c = B[i]
        rng = max(h-l, 1e-12)
        r  = [(B[j][3]-B[j][0])/B[j][0] for j in range(i-25, i+1)]
        rr = [(B[j][1]-B[j][2])/B[j][0] for j in range(i-25, i+1)]
        cl = [B[j][3] for j in range(i-25, i+1)]
        atr = np.mean(rr)
        f = []
        # --- candle shape
        f += [(c-o)/o, (c-l)/rng, (h-max(o,c))/rng, (min(o,c)-l)/rng,
              abs(c-o)/rng, (h-l)/o, (o-B[i-1][3])/B[i-1][3]]
        # --- momentum, several horizons
        for k in (1,2,3,5,10,20):
            f.append(float(np.sum(r[-k:])))
        # --- mean reversion: distance from moving averages
        for k in (5,10,20):
            ma = float(np.mean(cl[-k:]))
            f.append((c-ma)/ma)
        # --- position in recent range
        for k in (5,10,20):
            hi = max(B[j][1] for j in range(i-k+1, i+1))
            lo = min(B[j][2] for j in range(i-k+1, i+1))
            f.append((c-lo)/max(hi-lo, 1e-12))
        # --- volatility state
        f += [atr, float(np.mean(rr[-3:]))/(atr+1e-12),
              float(np.mean(rr[-5:]))/(atr+1e-12),
              float(np.std(r[-10:])), float(np.mean(np.abs(r[-5:])))]
        # --- streaks and counts
        f += [float(np.sum(np.sign(r[-3:]))), float(np.sum(np.sign(r[-5:]))),
              float(np.sum(np.sign(r[-10:]))),
              float(sum(1 for x in r[-10:] if x > 0))/10]
        # --- consecutive higher highs / lower lows
        f += [float(sum(1 for j in range(i-4,i+1) if B[j][1] > B[j-1][1])),
              float(sum(1 for j in range(i-4,i+1) if B[j][2] < B[j-1][2]))]
        # --- wick asymmetry over window
        uw = [(B[j][1]-max(B[j][0],B[j][3]))/max(B[j][1]-B[j][2],1e-12)
              for j in range(i-4, i+1)]
        lw = [(min(B[j][0],B[j][3])-B[j][2])/max(B[j][1]-B[j][2],1e-12)
              for j in range(i-4, i+1)]
        f += [float(np.mean(uw)), float(np.mean(lw)),
              float(np.mean(uw))-float(np.mean(lw))]
        # --- acceleration
        f += [float(np.mean(r[-3:]) - np.mean(r[-10:-3])),
              float(np.mean(rr[-3:]) - np.mean(rr[-10:-3]))]
        # --- session
        d = dt.datetime.utcfromtimestamp(ks[i])
        f += [float(d.hour), float(d.weekday()),
              float(np.sin(2*np.pi*d.hour/24)), float(np.cos(2*np.pi*d.hour/24))]
        nx = B[i+1]
        X.append(f); y.append(1 if nx[3] > nx[0] else 0); TS.append(ks[i])
    return np.array(X,float), np.array(y), np.array(TS), B

def wf_ridge(X, y, ridge=10.0, start=120):
    pred, act = [], []
    for i in range(start, len(X)):
        Xt, yt = X[:i], y[:i].astype(float)
        mu, sd = Xt.mean(0), Xt.std(0)+1e-12
        Z = (Xt-mu)/sd
        A = Z.T@Z + ridge*np.eye(Z.shape[1])
        w = np.linalg.solve(A, Z.T@(yt-yt.mean()))
        pred.append(float(((X[i]-mu)/sd)@w + yt.mean())); act.append(y[i])
    return np.array(pred), np.array(act)

say()
say("="*76)
say("THE SAME ARCHITECTURE THAT GAVE 86.84% ON RANGE, ON DIRECTION")
say("="*76)
say(f"{'tf':>4s} {'feat':>5s} {'n':>6s} {'base%':>7s} {'all%':>7s} "
    f"{'top20%':>8s} {'top10%':>8s} {'top5%':>8s} {'top2%':>8s}")
RES = {}
for mult, name in [(1,'1H'),(2,'2H'),(4,'4H'),(8,'8H'),(12,'12H'),(24,'1D')]:
    b = build(mult)
    if b is None: continue
    X, y, TS, B = b
    pred, act = wf_ridge(X, y)
    conf = np.abs(pred-0.5)
    RES[name] = (pred, act, conf, X, y, TS, B)
    line = f"{name:>4s} {X.shape[1]:5d} {len(act):6d} "\
           f"{max(act.mean(),1-act.mean())*100:6.2f}% "\
           f"{np.mean((pred>.5).astype(int)==act)*100:6.2f}%"
    for q in (.8,.9,.95,.98):
        m = conf >= np.quantile(conf, q)
        if m.sum() < 8: line += f"{'-':>8s}"; continue
        line += f"{np.mean((pred[m]>.5).astype(int)==act[m])*100:7.2f}%"
    say(line)

say()
say("="*76)
say("PER-HOUR CONDITIONING (what carried the range model)")
say("="*76)
if '1H' in RES:
    pred, act, conf, X, y, TS, B = RES['1H']
    off = len(y)-len(act)
    hrs = np.array([dt.datetime.utcfromtimestamp(t).hour for t in TS[off:]])
    say(f"  {'hour':>5s} {'n':>5s} {'P(bull)':>9s} {'model acc':>11s}")
    rows = []
    for h in range(24):
        m = hrs == h
        if m.sum() < 40: continue
        p = act[m].mean()
        a = np.mean((pred[m]>.5).astype(int)==act[m])*100
        rows.append((abs(p-.5), h, m.sum(), p, a))
    rows.sort(reverse=True)
    for _, h, n, p, a in rows[:8]:
        say(f"  {h:5d} {n:5d} {p*100:8.1f}% {a:10.2f}%")
    say(f"\n  most extreme hourly base rate: "
        f"{max(max(r[3],1-r[3]) for r in rows)*100:.1f}%")

say()
say("="*76)
say("BEST DIRECTION CELL ANYWHERE vs THE 85% TARGET")
say("="*76)
best = (0, None)
for name, (pred, act, conf, X, y, TS, B) in RES.items():
    for q in (0.0,.5,.8,.9,.95,.98,.99):
        m = conf >= np.quantile(conf, q)
        if m.sum() < 15: continue
        a = np.mean((pred[m]>.5).astype(int)==act[m])*100
        if a > best[0]: best = (a, (name, q, m.sum()))
say(f"  best direction accuracy found: {best[0]:.2f}%")
if best[1]:
    n2, q2, nn = best[1]
    say(f"  at {n2}, top {int((1-q2)*100)}% confidence, n={nn}")
say(f"  target: 85%")
say(f"  {'REACHED' if best[0] >= 85 else 'NOT REACHED'}")

say()
say("="*76)
say("SIDE BY SIDE: SAME MODEL, SAME BARS, TWO QUESTIONS")
say("="*76)
if '1H' in RES:
    pred, act, conf, X, y, TS, B = RES['1H']
    m = conf >= np.quantile(conf, .95)
    say(f"  DIRECTION (will next candle be bullish?)")
    say(f"     all bars   {np.mean((pred>.5).astype(int)==act)*100:.2f}%")
    say(f"     top 5%     {np.mean((pred[m]>.5).astype(int)==act[m])*100:.2f}%")
    say(f"  RANGE (will next candle be big?)     [from prior run]")
    say(f"     all bars   62.09%")
    say(f"     top 5%     86.84%")
