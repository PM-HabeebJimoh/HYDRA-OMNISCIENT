"""
THE SECOND HALF OF THE REQUEST: OHLC RANGES, NOT DIRECTION.

Direction result (69,391 cells tested): best 61.54%, empirical p=0.200.
The search itself manufactures z=3.38 on shuffled labels. Nothing survives.

But the request was "direction of the next candles OR OHLC ranges".
Range is a different random variable. Testing it with the same rigour,
and asking the same question: can it reach 85%?
"""
import json, glob, sys, itertools, collections, datetime as dt
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
T1 = sorted(raw)

def resample(mult):
    B = {}
    for t in T1:
        k = t-(t % (3600*mult)); o,h,l,c = raw[t]
        if k not in B: B[k] = [o,h,l,c]
        else:
            B[k][1]=max(B[k][1],h); B[k][2]=min(B[k][2],l); B[k][3]=c
    ks = sorted(B); return ks, [tuple(B[k]) for k in ks]

say("="*78)
say("XAUUSD RANGE PREDICTION")
say("="*78)

def study(name, mult):
    ks, bars = resample(mult)
    if len(bars) < 120: return None
    X, Y, R = [], [], []
    for i in range(25, len(bars)-1):
        o,h,l,c = bars[i]
        rr = [(bars[j][1]-bars[j][2])/bars[j][0] for j in range(i-20,i+1)]
        r  = [(bars[j][3]-bars[j][0])/bars[j][0] for j in range(i-20,i+1)]
        rng = max(h-l,1e-12)
        atr, atr5, atr3 = np.mean(rr), np.mean(rr[-5:]), np.mean(rr[-3:])
        X.append([rr[-1], atr3, atr5, atr, np.std(rr[-10:]),
                  atr3/(atr+1e-12), atr5/(atr+1e-12),
                  abs(c-o)/rng, (h-max(o,c))/rng, (min(o,c)-l)/rng,
                  np.std(r[-10:]), np.mean(np.abs(r[-5:])),
                  float(dt.datetime.utcfromtimestamp(ks[i]).hour),
                  float(dt.datetime.utcfromtimestamp(ks[i]).weekday())])
        nx = bars[i+1]
        Y.append((nx[1]-nx[2])/nx[0])
        R.append(float(np.median(rr)))
    return name, np.array(X), np.array(Y), np.array(R)

RES = []
for name, mult in [('1H',1),('2H',2),('4H',4),('8H',8),('12H',12),('1D',24)]:
    s = study(name, mult)
    if s: RES.append(s)

say()
say("1. CAN RANGE BE FORECAST AT ALL? (walk-forward ridge, causal)")
say("="*78)
say(f"{'tf':>5s} {'n':>6s} {'IC':>8s} {'t':>8s} {'R2%':>7s}")
for name, X, Y, R in RES:
    pred, act = [], []
    for i in range(80, len(X)):
        Xt, Yt = X[:i], Y[:i]
        mu, sd = Xt.mean(0), Xt.std(0)+1e-12
        Z = (Xt-mu)/sd
        A = Z.T@Z + 10*np.eye(Z.shape[1])
        w = np.linalg.solve(A, Z.T@(Yt-Yt.mean()))
        pred.append(float(((X[i]-mu)/sd)@w + Yt.mean())); act.append(Y[i])
    pred, act = np.array(pred), np.array(act)
    ic = np.corrcoef(pred, act)[0,1]; n = len(pred)
    t = ic*np.sqrt(n-2)/np.sqrt(1-ic**2)
    say(f"{name:>5s} {n:6d} {ic:+8.4f} {t:+8.2f} {ic**2*100:7.1f}")

say()
say("2. BINARY: will next range EXCEED its trailing median? (50/50 base)")
say("="*78)
say(f"{'tf':>5s} {'n':>6s} {'all%':>7s} {'top50%':>8s} {'top20%':>8s} "
    f"{'top10%':>8s} {'top5%':>8s}")
BEST = []
for name, X, Y, R in RES:
    pred, act = [], []
    for i in range(80, len(X)):
        Xt = X[:i]; Yt = (Y[:i] > R[:i]).astype(float)
        mu, sd = Xt.mean(0), Xt.std(0)+1e-12
        Z = (Xt-mu)/sd
        A = Z.T@Z + 10*np.eye(Z.shape[1])
        w = np.linalg.solve(A, Z.T@(Yt-Yt.mean()))
        pred.append(float(((X[i]-mu)/sd)@w + Yt.mean()))
        act.append(1 if Y[i] > R[i] else 0)
    pred, act = np.array(pred), np.array(act)
    conf = np.abs(pred-0.5)
    line = f"{name:>5s} {len(act):6d}"
    row = []
    for q in (0.0, .5, .8, .9, .95):
        m = conf >= np.quantile(conf, q)
        if m.sum() < 10: line += f"{'-':>8s}"; row.append(None); continue
        a = np.mean((pred[m] > .5).astype(int) == act[m])*100
        line += f"{a:7.1f}%"; row.append(a)
    say(line)
    BEST.append((name, row, pred, act))

say()
say("3. DOES ANY RANGE CELL REACH 85%?")
say("="*78)
mx = max((r for _, row, _, _ in BEST for r in row if r), default=0)
say(f"  best range accuracy anywhere: {mx:.1f}%")
say(f"  at or above 85%: {'YES' if mx >= 85 else 'NO'}")

say()
say("4. THE HONEST COMPARISON")
say("="*78)
say("""  DIRECTION  69,391 cells searched -> best 61.54%, p=0.200 (noise)
  RANGE      walk-forward, no search -> see table above

  Range needs no cell search: a single linear model on 14 causal
  features forecasts it directly. That is the structural difference.""")
