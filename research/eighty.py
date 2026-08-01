"""
WHERE IS >80% ACCURACY ACTUALLY REACHABLE?

The combination model settled the direction question:
  84 features, 9 layers, 3 model families, walk-forward, 802 OOS bars
  gold 50.4/50.4/50.6/49.3 | eur 49.3/52.7/52.9/53.4 | aud 49.3/52.6/49.9/50.1
  Confidence filter does NOT rise -- gold gb top-5% = 36.6%, WORSE than chance.
  Same features on MAGNITUDE: IC +0.47..+0.52, t=+15..+17, R2 22-27%.

Same rows. Same features. Same models. Same day.
Direction ~50%. Magnitude t=+17. The difference is the TARGET, not the effort.

So: 80% accuracy is reachable -- but only on questions the market does not
pay anyone to destroy. This script measures exactly which questions, and
whether the answers are worth money.

Q1 Will the next bar's range EXCEED its recent median?      (binary magnitude)
Q2 Will price touch +X ATR before -X ATR? (direction, control)
Q3 Will the bar be a BIG mover (top-quartile range)?
Q4 Does an 80%-accurate magnitude call convert into money?
"""
import json, sys, glob, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events, tstat, signflip_null
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def say(*a): print(*a, flush=True)

p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4)
MAC = {}
for f in glob.glob(str(ROOT / 'data/raw/macro/*.json')):
    d = json.load(open(f))
    MAC[Path(f).stem] = {dt.date.fromisoformat(x): v
                         for x, v in zip(d['dates'], d['v']) if v is not None}
MKEYS = ('VIX', 'DXY', 'HYSPREAD', 'CURVE', 'GVZ', 'VIX3M')
MSORT = {k: sorted(MAC.get(k, {})) for k in MKEYS}
EV = build_events()
sched4 = collections.Counter(e['ts'] - (e['ts'] % 14400) for e in EV)

def macro_at(k, d, lag=1):
    cut, best = d - dt.timedelta(days=lag), None
    for x in MSORT[k]:
        if x <= cut: best = MAC[k][x]
        else: break
    return best

def series(a):
    out, pc = [], None
    for t in b4:
        x = p4[t][a]
        out.append((t, x['open'], x['high'], x['low'], x['close'],
                    pc if pc else x['open']))
        pc = x['close']
    return out
S = {a: series(a) for a in A}
SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}

def build(tgt):
    s = S[tgt]; X, rows = [], []
    for i in range(60, len(s) - 1):
        t = s[i][0]; d = dt.datetime.utcfromtimestamp(t).date(); f = []
        for a in A:
            q = S[a]; _, o, h, l, c, pc = q[i]
            rng = max(h - l, 1e-12)
            f += [(c-o)/o, (c-l)/rng, (h-max(o,c))/rng, (min(o,c)-l)/rng,
                  abs(c-o)/rng, rng/o]
            rr = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
            r = [(q[j][4]-q[j][1])/q[j][1] for j in range(i-20, i+1)]
            f += [np.mean(rr[-3:]), np.mean(rr[-5:]), np.mean(rr[-10:]),
                  np.mean(rr[-20:]), np.std(rr[-10:]),
                  np.mean(rr[-3:])/(np.mean(rr[-20:])+1e-12),
                  np.std(r[-10:]), np.mean(np.abs(r[-5:]))]
        for k in MKEYS:
            v = macro_at(k, d); f.append(v if v is not None else 0.0)
        f += [float(sched4.get(t, 0)), float(sched4.get(t+14400, 0)),
              float(dt.datetime.utcfromtimestamp(t).hour),
              float(dt.datetime.utcfromtimestamp(t).weekday())]
        q = S[tgt]
        hist = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
        nx = q[i+1]
        X.append(f)
        rows.append(dict(t=t, i=i,
                         nrng=(nx[2]-nx[3])/nx[1],
                         med=float(np.median(hist)),
                         q75=float(np.quantile(hist, .75)),
                         up=1 if nx[4] > nx[1] else 0))
    return np.array(X, float), rows

def wf(X, y, min_tr=150, refit=5):
    pr, tr = [], []
    mdl = sc = None
    for i in range(min_tr, len(X)):
        if (i-min_tr) % refit == 0:
            if len(np.unique(y[:i])) < 2: continue
            sc = StandardScaler().fit(X[:i])
            mdl = RandomForestClassifier(n_estimators=150, max_depth=6,
                                         min_samples_leaf=15, random_state=0,
                                         n_jobs=-1).fit(sc.transform(X[:i]), y[:i])
        if mdl is None: continue
        pr.append(float(mdl.predict_proba(sc.transform(X[i:i+1]))[0, 1]))
        tr.append(y[i])
    return np.array(pr), np.array(tr)

say("=" * 78)
say("WHICH QUESTIONS CAN BE ANSWERED AT >80%?")
say("=" * 78)
say(f"{'asset':6s} {'question':34s} {'base%':>7s} {'acc%':>7s} "
    f"{'top20%':>8s} {'top10%':>8s}")

DATA = {}
for a in A:
    X, rows = build(a)
    DATA[a] = (X, rows)
    for lab, y in [
        ('DIRECTION next bar up',
         np.array([r['up'] for r in rows])),
        ('MAGNITUDE range > med20',
         np.array([int(r['nrng'] > r['med']) for r in rows])),
        ('MAGNITUDE range > 75th pct',
         np.array([int(r['nrng'] > r['q75']) for r in rows])),
        ('MAGNITUDE range < med20 (quiet)',
         np.array([int(r['nrng'] < r['med']) for r in rows])),
    ]:
        pr, tr = wf(X, y)
        acc = np.mean((pr > .5).astype(int) == tr)*100
        base = max(tr.mean(), 1-tr.mean())*100
        conf = np.abs(pr-.5)
        line = f"{a:6s} {lab:34s} {base:7.1f} {acc:7.2f}"
        for q in (.8, .9):
            m = conf >= np.quantile(conf, q)
            aa = np.mean((pr[m] > .5).astype(int) == tr[m])*100
            line += f" {aa:7.1f}%"
        say(line)

say()
say("=" * 78)
say("THE HIGH-CONFIDENCE MAGNITUDE CALL: how accurate can it get?")
say("=" * 78)
for a in A:
    X, rows = DATA[a]
    y = np.array([int(r['nrng'] > r['med']) for r in rows])
    pr, tr = wf(X, y)
    conf = np.abs(pr - .5)
    say(f"\n  {a.upper()}  (base rate {max(tr.mean(),1-tr.mean())*100:.1f}%)")
    for q in (0.0, .5, .7, .8, .9, .95, .98):
        m = conf >= np.quantile(conf, q)
        if m.sum() < 5: continue
        aa = np.mean((pr[m] > .5).astype(int) == tr[m])*100
        say(f"    top {int((1-q)*100):>3d}% most confident  n={m.sum():4d}  "
            f"accuracy {aa:5.1f}%")

say()
say("=" * 78)
say("DOES THE 80% MAGNITUDE CALL MAKE MONEY? (straddle, worst-case whipsaw)")
say("=" * 78)
say("Buy a bracket only when the model is confident the range will be LARGE.")
for a in A:
    X, rows = DATA[a]
    y = np.array([int(r['nrng'] > r['q75']) for r in rows])
    pr, tr = wf(X, y)
    off = len(rows) - len(pr)
    sub = rows[off:]
    q = S[a]
    conf = pr                                   # prob of a big bar
    for thr_q in (0.0, .5, .8, .9):
        thr = np.quantile(conf, thr_q)
        pnl = []
        for k, r in enumerate(sub):
            if conf[k] < thr: continue
            i = r['i']
            hist = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
            w = float(np.mean(hist))            # bracket = mean past range
            _, o, h, l, c, _ = q[i+1]
            up, dn = o*(1+w), o*(1-w)
            hs = SPREAD[a]
            if h >= up and l <= dn:  v = -2*w - 2*hs
            elif h >= up:            v = (c-up)/o - hs
            elif l <= dn:            v = (dn-c)/o - hs
            else:                    continue
            pnl.append(v)
        if len(pnl) < 10: continue
        m, t, n = tstat(pnl)
        say(f"  {a:5s} top {int((1-thr_q)*100):>3d}% predicted-big  n={n:4d}  "
            f"mean {m*100:+.4f}%  t={t:+5.2f}  "
            f"WR {np.mean([x>0 for x in pnl])*100:.1f}%")
