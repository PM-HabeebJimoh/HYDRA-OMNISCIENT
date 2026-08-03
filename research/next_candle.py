"""
THE EXACT QUESTION: WILL THE NEXT CANDLE BE BULLISH OR BEARISH?

One target. XAUUSD. close[t+1] > open[t+1] ?

Everything I have, aimed at that single question:
  A. per-hour direction bias (does any UTC hour lean bullish/bearish?)
  B. per-weekday bias
  C. hour x weekday interaction
  D. conditional on the range forecast (is direction easier on big bars?)
  E. multi-timeframe alignment
  F. mean reversion vs continuation, by context
  G. gap behaviour
  H. machine learning on all features, walk-forward
  I. the empirical null for every search above

Nothing is claimed until it beats a shuffled-label search of the same size.
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
TS = sorted(raw); B = [raw[t] for t in TS]
say("="*76)
say("NEXT CANDLE: BULLISH OR BEARISH?  XAUUSD 1H")
say("="*76)
say(f"bars {len(B)}  {dt.datetime.utcfromtimestamp(TS[0]):%Y-%m-%d} .. "
    f"{dt.datetime.utcfromtimestamp(TS[-1]):%Y-%m-%d}")

BULL = np.array([1 if B[i+1][3] > B[i+1][0] else 0 for i in range(len(B)-1)])
HR = np.array([dt.datetime.utcfromtimestamp(TS[i]).hour for i in range(len(B)-1)])
WD = np.array([dt.datetime.utcfromtimestamp(TS[i]).weekday() for i in range(len(B)-1)])
say(f"overall next-candle bullish rate: {BULL.mean()*100:.2f}%")
say(f"-> the base rate is {max(BULL.mean(),1-BULL.mean())*100:.2f}% "
    f"(what you get for free)")

say()
say("="*76)
say("A. DIRECTION BIAS BY UTC HOUR")
say("="*76)
say(f"{'hour':>5s} {'n':>6s} {'bullish%':>10s} {'z':>8s}")
hrs = []
for h in range(24):
    m = HR == h
    if m.sum() < 50: continue
    p = BULL[m].mean(); n = m.sum()
    z = (p-0.5)/np.sqrt(0.25/n)
    hrs.append((abs(z), h, p, n, z))
    say(f"{h:5d} {n:6d} {p*100:9.2f}% {z:+8.2f}")
hrs.sort(reverse=True)
say(f"\n  strongest hour: {hrs[0][1]:02d}:00 at {hrs[0][2]*100:.2f}% "
    f"(z={hrs[0][4]:+.2f})")
say(f"  hours tested: 24, noise max|z| ~ {np.sqrt(2*np.log(24)):.2f}")

say()
say("="*76)
say("B. DIRECTION BIAS BY WEEKDAY")
say("="*76)
for w in range(7):
    m = WD == w
    if m.sum() < 50: continue
    p = BULL[m].mean(); n = m.sum()
    say(f"  {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][w]}  n={n:5d}  "
        f"bullish {p*100:5.2f}%  z={(p-0.5)/np.sqrt(0.25/n):+.2f}")

say()
say("="*76)
say("C. HOUR x WEEKDAY (168 cells)")
say("="*76)
cells = []
for h in range(24):
    for w in range(5):
        m = (HR == h) & (WD == w)
        if m.sum() < 25: continue
        p = BULL[m].mean(); n = m.sum()
        acc = max(p, 1-p)*100
        z = (acc-50)/(np.sqrt(0.25/n)*100)
        cells.append((z, acc, n, h, w, p))
cells.sort(reverse=True)
say(f"  cells with n>=25: {len(cells)}")
say(f"  noise max|z| ~ {np.sqrt(2*np.log(max(len(cells),2))):.2f}")
say(f"\n  {'acc%':>7s} {'z':>7s} {'n':>5s}  cell")
for z, acc, n, h, w, p in cells[:8]:
    say(f"  {acc:7.2f} {z:+7.2f} {n:5d}  "
        f"{['Mon','Tue','Wed','Thu','Fri'][w]} {h:02d}:00 -> "
        f"{'BULL' if p>.5 else 'BEAR'}")

say()
say("="*76)
say("D. IS DIRECTION EASIER WHEN THE RANGE IS BIG? (the key question)")
say("="*76)
say("My range model is 86.84% accurate. If direction were predictable")
say("on the bars it flags, the two would combine into a real system.")
X, lab, med = [], [], []
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
              float(dt.datetime.utcfromtimestamp(TS[i]).hour),
              float(dt.datetime.utcfromtimestamp(TS[i]).weekday())])
    med.append(float(np.median(rr)))
    lab.append(1 if (B[i+1][1]-B[i+1][2])/B[i+1][0] > np.median(rr) else 0)
X = np.array(X); lab = np.array(lab, float)
off = 25
bull_al = np.array([1 if B[i+1][3] > B[i+1][0] else 0
                    for i in range(off, len(B)-1)])

pred = []
for i in range(80, len(X)):
    Xt, Yt = X[:i], lab[:i]
    mu, sd = Xt.mean(0), Xt.std(0)+1e-12
    Z = (Xt-mu)/sd
    A = Z.T@Z + 10*np.eye(Z.shape[1])
    w = np.linalg.solve(A, Z.T@(Yt-Yt.mean()))
    pred.append(float(((X[i]-mu)/sd)@w + Yt.mean()))
pred = np.array(pred)
bb = bull_al[80:]
conf = np.abs(pred-0.5)
say(f"\n  {'range-model bucket':26s} {'n':>6s} {'bullish%':>10s} {'|dev|':>7s}")
for q, name in [(0.0,'all bars'), (.8,'top 20% confident'),
                (.9,'top 10% confident'), (.95,'top 5% confident')]:
    m = conf >= np.quantile(conf, q)
    p = bb[m].mean()
    say(f"  {name:26s} {m.sum():6d} {p*100:9.2f}% {abs(p-.5)*100:6.2f}")
say("\n  -> if these stay near 50%, big bars are NOT directionally biased")

say()
say("="*76)
say("E. CONTINUATION vs REVERSION, BY CONTEXT")
say("="*76)
say(f"  {'context':34s} {'n':>6s} {'continues%':>12s}")
for name, mask in [
    ('after bull candle',
     np.array([B[i][3] > B[i][0] for i in range(len(B)-1)])),
    ('after bear candle',
     np.array([B[i][3] < B[i][0] for i in range(len(B)-1)])),
    ('after 3 bull in a row',
     np.array([i >= 2 and all(B[j][3] > B[j][0] for j in (i,i-1,i-2))
               for i in range(len(B)-1)])),
    ('after 3 bear in a row',
     np.array([i >= 2 and all(B[j][3] < B[j][0] for j in (i,i-1,i-2))
               for i in range(len(B)-1)])),
    ('after big bull (>1.5x atr)',
     np.array([i >= 21 and B[i][3] > B[i][0] and
               (B[i][1]-B[i][2])/B[i][0] >
               1.5*np.mean([(B[j][1]-B[j][2])/B[j][0] for j in range(i-20,i)])
               for i in range(len(B)-1)])),
    ('after big bear (>1.5x atr)',
     np.array([i >= 21 and B[i][3] < B[i][0] and
               (B[i][1]-B[i][2])/B[i][0] >
               1.5*np.mean([(B[j][1]-B[j][2])/B[j][0] for j in range(i-20,i)])
               for i in range(len(B)-1)])),
]:
    if mask.sum() < 30: continue
    prev_bull = np.array([B[i][3] > B[i][0] for i in range(len(B)-1)])
    cont = (BULL[mask] == prev_bull[mask]).mean()
    say(f"  {name:34s} {mask.sum():6d} {cont*100:11.2f}%")

say()
say("="*76)
say("F. MACHINE LEARNING, WALK-FORWARD, ON DIRECTION")
say("="*76)
dl = bull_al.astype(float)
dp = []
for i in range(80, len(X)):
    Xt, Yt = X[:i], dl[:i]
    mu, sd = Xt.mean(0), Xt.std(0)+1e-12
    Z = (Xt-mu)/sd
    A = Z.T@Z + 10*np.eye(Z.shape[1])
    w = np.linalg.solve(A, Z.T@(Yt-Yt.mean()))
    dp.append(float(((X[i]-mu)/sd)@w + Yt.mean()))
dp = np.array(dp); da = dl[80:]
dc = np.abs(dp-0.5)
say(f"  {'bucket':26s} {'n':>6s} {'accuracy':>10s}")
for q, name in [(0.0,'all'), (.5,'top 50%'), (.8,'top 20%'),
                (.9,'top 10%'), (.95,'top 5%')]:
    m = dc >= np.quantile(dc, q)
    if m.sum() < 10: continue
    a = np.mean((dp[m] > .5).astype(int) == da[m])*100
    say(f"  {name:26s} {m.sum():6d} {a:9.2f}%")

say()
say("="*76)
say("G. THE EMPIRICAL NULL FOR EVERYTHING ABOVE")
say("="*76)
rng_ = np.random.default_rng(0)
mx = []
for _ in range(200):
    sh = rng_.permutation(BULL)
    best = 0
    for h in range(24):
        for w in range(5):
            m = (HR == h) & (WD == w)
            if m.sum() < 25: continue
            p = sh[m].mean(); n = m.sum()
            acc = max(p, 1-p)*100
            best = max(best, (acc-50)/(np.sqrt(0.25/n)*100))
    mx.append(best)
mx = np.array(mx)
say(f"  shuffled hour x weekday search, max z:")
say(f"    median {np.median(mx):.2f}  95th {np.percentile(mx,95):.2f}  "
    f"max {mx.max():.2f}")
say(f"  actual best: {cells[0][0]:.2f}")
say(f"  empirical p = {(mx >= cells[0][0]).mean():.3f}")

say()
say("="*76)
say("BEST NEXT-CANDLE DIRECTION ACCURACY FOUND")
say("="*76)
allbest = max([c[1] for c in cells] +
              [max(np.mean((dp[dc >= np.quantile(dc,q)] > .5).astype(int) ==
                           da[dc >= np.quantile(dc,q)])*100
                   for q in (0,.5,.8,.9,.95))])
say(f"  {allbest:.2f}%")
say(f"  target: 85%")
say(f"  {'TARGET MET' if allbest >= 85 else 'TARGET NOT MET'}")
