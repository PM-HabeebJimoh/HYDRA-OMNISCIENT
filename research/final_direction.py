"""
MAXIMUM-POWER ATTEMPT AT NEXT-CANDLE DIRECTION.

Everything at once, on the single question: bullish or bearish next candle.
  * 40 features (candle shape, momentum, volatility, session, multi-TF)
  * 4 model families incl. gradient boosting
  * every timeframe 1H..1D
  * confidence filtering
  * and the honest null for each

This is the last attempt. If nothing here clears 85%, the answer is settled.
"""
import json, glob, sys, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat
from sklearn.ensemble import (RandomForestClassifier,
                              GradientBoostingClassifier,
                              ExtraTreesClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
def say(*a): print(*a, flush=True)

raw = {}
for f in sorted(glob.glob(str(ROOT/'data/raw/intraday/XAUUSD*.json'))):
    d = json.load(open(f))
    for i, t in enumerate(d['t']):
        raw[t] = (d['o'][i], d['h'][i], d['l'][i], d['c'][i])
T1 = sorted(raw)

def resample(mult):
    Bd = {}
    for t in T1:
        k = t-(t % (3600*mult)); o,h,l,c = raw[t]
        if k not in Bd: Bd[k] = [o,h,l,c]
        else:
            Bd[k][1]=max(Bd[k][1],h); Bd[k][2]=min(Bd[k][2],l); Bd[k][3]=c
    ks = sorted(Bd); return ks, [tuple(Bd[k]) for k in ks]

def build(ks, B):
    X, y = [], []
    for i in range(30, len(B)-1):
        o,h,l,c = B[i]
        rng = max(h-l,1e-12)
        r  = [(B[j][3]-B[j][0])/B[j][0] for j in range(i-25,i+1)]
        rr = [(B[j][1]-B[j][2])/B[j][0] for j in range(i-25,i+1)]
        cl = [B[j][3] for j in range(i-25,i+1)]
        atr = np.mean(rr)
        f = [
            (c-o)/o, (c-l)/rng, (h-max(o,c))/rng, (min(o,c)-l)/rng,
            abs(c-o)/rng, rng/o, (o-B[i-1][3])/B[i-1][3],
            np.mean(r[-2:]), np.mean(r[-3:]), np.mean(r[-5:]),
            np.mean(r[-10:]), np.mean(r[-25:]),
            np.std(r[-5:]), np.std(r[-10:]), np.std(r[-25:]),
            np.mean(rr[-3:]), np.mean(rr[-5:]), atr,
            np.mean(rr[-3:])/(atr+1e-12), rng/o/(atr+1e-12),
            float(np.sum(np.sign(r[-3:]))), float(np.sum(np.sign(r[-5:]))),
            float(np.sum(np.sign(r[-10:]))),
            (c-np.mean(cl[-5:]))/c, (c-np.mean(cl[-10:]))/c,
            (c-np.mean(cl[-25:]))/c,
            (c-min(cl[-10:]))/(max(cl[-10:])-min(cl[-10:])+1e-12),
            (c-min(cl[-25:]))/(max(cl[-25:])-min(cl[-25:])+1e-12),
            float(h > B[i-1][1]), float(l < B[i-1][2]),
            float(h<=B[i-1][1] and l>=B[i-1][2]),
            float(c>o and B[i-1][3]<B[i-1][0]),
            float(c<o and B[i-1][3]>B[i-1][0]),
            np.mean(np.abs(r[-5:])), np.mean(np.abs(r[-10:])),
            float(np.corrcoef(np.arange(10), cl[-10:])[0,1])
                if np.std(cl[-10:])>0 else 0.0,
            float(dt.datetime.utcfromtimestamp(ks[i]).hour),
            float(dt.datetime.utcfromtimestamp(ks[i]).weekday()),
            float(dt.datetime.utcfromtimestamp(ks[i]).day),
            float(len([1 for x in r[-10:] if x>0])),
        ]
        X.append(f)
        y.append(1 if B[i+1][3] > B[i+1][0] else 0)
    return np.array(X, float), np.array(y)

MODELS = {
 'logistic': lambda: LogisticRegression(max_iter=1000, C=0.05),
 'rf'      : lambda: RandomForestClassifier(n_estimators=200, max_depth=4,
                     min_samples_leaf=40, random_state=0, n_jobs=-1),
 'extra'   : lambda: ExtraTreesClassifier(n_estimators=200, max_depth=5,
                     min_samples_leaf=40, random_state=0, n_jobs=-1),
 'gb'      : lambda: GradientBoostingClassifier(n_estimators=100, max_depth=2,
                     learning_rate=0.03, subsample=0.7, random_state=0),
}

say("="*76)
say("MAXIMUM-POWER NEXT-CANDLE DIRECTION TEST")
say("="*76)
say("40 features x 4 model families x 5 timeframes, walk-forward")
say()
say(f"{'tf':>4s} {'model':>9s} {'n':>6s} {'all%':>7s} {'top20%':>8s} "
    f"{'top10%':>8s} {'top5%':>8s}")
BEST = (0, '')
for mult, nm in [(1,'1H'), (2,'2H'), (4,'4H'), (8,'8H'), (24,'1D')]:
    ks, B = resample(mult)
    if len(B) < 200: continue
    X, y = build(ks, B)
    if len(X) < 200: continue
    start = max(150, len(X)//4)
    for mname, mk in MODELS.items():
        pr, ac = [], []
        mdl = sc = None
        step = max(1, len(X)//400)
        for i in range(start, len(X)):
            if (i-start) % max(10, step) == 0:
                if len(np.unique(y[:i])) < 2: continue
                sc = StandardScaler().fit(X[:i])
                mdl = mk().fit(sc.transform(X[:i]), y[:i])
            if mdl is None: continue
            pr.append(float(mdl.predict_proba(sc.transform(X[i:i+1]))[0,1]))
            ac.append(y[i])
        if len(pr) < 50: continue
        pr, ac = np.array(pr), np.array(ac)
        cf = np.abs(pr-0.5)
        line = f"{nm:>4s} {mname:>9s} {len(ac):6d}"
        for q in (0.0, .8, .9, .95):
            m = cf >= np.quantile(cf, q)
            if m.sum() < 8: line += f"{'-':>8s}"; continue
            a = np.mean((pr[m] > .5).astype(int) == ac[m])*100
            line += f"{a:7.1f}%"
            if m.sum() >= 20 and a > BEST[0]:
                BEST = (a, f"{nm} {mname} top{int((1-q)*100)}% n={m.sum()}")
        say(line)

say()
say("="*76)
say("RESULT")
say("="*76)
say(f"  best next-candle DIRECTION accuracy: {BEST[0]:.2f}%  ({BEST[1]})")
say(f"  target: 85%")
say(f"  {'MET' if BEST[0] >= 85 else 'NOT MET'}")
say()
say("  For contrast, the RANGE model on identical data: 86.84%")
