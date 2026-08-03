"""
THE COMBINATION MODEL (fast, unbuffered).

Fair criticism: 34 signals were tested ONE AT A TIME. A feature can be
individually worthless (t~0) yet valuable inside a combination, through
interaction, conditioning or nonlinearity. That was never properly tested.

All nine layers in one matrix, walk-forward:
  L1 price/return structure   L2 microstructure (CLV/wicks/gaps/dispersion)
  L3 macro levels (FRED)      L4 macro changes
  L5 implied vol + VRP        L6 cross-market ratios
  L7 calendar SCHEDULE (incl. NEXT bar's schedule -- known days ahead)
  L8 calendar surprise/ex-ante
  L9 CFTC positioning (published-Friday lag)

Targets: DIRECTION (sign of next bar) and MAGNITUDE (next-bar range).
"""
import json, sys, glob, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (RandomForestClassifier,
                              GradientBoostingClassifier,
                              RandomForestRegressor)
from sklearn.preprocessing import StandardScaler

def say(*a):
    print(*a, flush=True)

p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4)
say(f"4H bars: {len(b4)}  "
    f"{dt.datetime.utcfromtimestamp(b4[0]):%Y-%m-%d} .. "
    f"{dt.datetime.utcfromtimestamp(b4[-1]):%Y-%m-%d}")

MAC = {}
for f in glob.glob(str(ROOT / 'data/raw/macro/*.json')):
    d = json.load(open(f))
    MAC[Path(f).stem] = {dt.date.fromisoformat(x): v
                         for x, v in zip(d['dates'], d['v']) if v is not None}
MKEYS = ('VIX', 'DXY', 'HYSPREAD', 'CURVE', 'GVZ', 'VIX3M')
MSORT = {k: sorted(MAC.get(k, {})) for k in MKEYS}
say("macro:", ", ".join(sorted(MAC)))

EV = build_events()
sched4 = collections.Counter(e['ts'] - (e['ts'] % 14400) for e in EV)
surp4, exante4 = collections.defaultdict(float), collections.defaultdict(float)
for e in EV:
    k = e['ts'] - (e['ts'] % 14400)
    if e.get('surp_z') is not None:
        surp4[k] += float(np.clip(e['surp_z'], -3, 3))
    if e.get('exante') is not None:
        exante4[k] += float(np.sign(e['exante']))

COT = json.load(open(ROOT / 'data/raw/cot/cot_3assets.json'))
cot = {}
for a in A:
    rows, hist = COT[a], []
    cot[a] = []
    for k, (ds, nl, ns, cl, cs, oi) in enumerate(rows):
        net = nl - ns
        pct = float(np.mean([h < net for h in hist])) if len(hist) >= 12 else .5
        dnet = net - (rows[k-1][1] - rows[k-1][2]) if k else 0.0
        cot[a].append((dt.date.fromisoformat(ds) + dt.timedelta(days=3),
                       pct, net / oi, np.sign(dnet), np.sign(cl - cs)))
        hist.append(net)

def cot_at(a, d):
    best = (0.5, 0.0, 0.0, 0.0)
    for pub, pct, noi, fl, cm in cot[a]:
        if pub < d: best = (pct, noi, fl, cm)
        else: break
    return best

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

def build(tgt):
    s = S[tgt]; X, yd, ym, T = [], [], [], []
    for i in range(60, len(s) - 1):
        t = s[i][0]; d = dt.datetime.utcfromtimestamp(t).date(); f = []
        for a in A:
            q = S[a]; _, o, h, l, c, pc = q[i]
            rng = max(h - l, 1e-12)
            f += [(c-o)/o, (c-l)/rng, (h-max(o,c))/rng, (min(o,c)-l)/rng,
                  abs(c-o)/rng, (o-q[i-1][4])/q[i-1][4], rng/o]
            r = [(q[j][4]-q[j][1])/q[j][1] for j in range(i-20, i+1)]
            rr = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
            f += [np.mean(r[-3:]), np.mean(r[-10:]), np.std(r[-10:]),
                  np.mean(rr[-5:]), np.mean(rr[-20:]), np.std(rr[-10:]),
                  np.mean(rr[-5:])/(np.mean(rr[-20:])+1e-12),
                  float(np.sum(np.sign(r[-5:])))]
        bod = [(S[a][i][4]-S[a][i][1])/S[a][i][1] for a in A]
        f += [float(np.std(bod)), float(np.mean(bod)),
              float(np.sum(np.sign(bod))),
              float(abs(np.sum(np.sign(bod))) == 3)]
        lv = {}
        for k in MKEYS:
            v = macro_at(k, d); lv[k] = v; f.append(v if v is not None else 0.0)
        for k in MKEYS:
            a5 = macro_at(k, d, 6)
            f.append((lv[k]-a5)/(abs(a5)+1e-9)
                     if (lv[k] is not None and a5) else 0.0)
        g, v_, v3, hy = lv['GVZ'], lv['VIX'], lv['VIX3M'], lv['HYSPREAD']
        f += [g/v_ if (g and v_) else 0.0, v3/v_ if (v3 and v_) else 0.0,
              hy/v_ if (hy and v_) else 0.0]
        rg = [(S['gold'][j][4]-S['gold'][j][1])/S['gold'][j][1]
              for j in range(i-20, i+1)]
        rv = float(np.std(rg))*np.sqrt(6*252)*100
        f += [rv, (g-rv) if g else 0.0]
        f += [float(sched4.get(t, 0)), float(sched4.get(t+14400, 0)),
              float(surp4.get(t, 0.0)), float(exante4.get(t+14400, 0.0)),
              float(dt.datetime.utcfromtimestamp(t).hour),
              float(dt.datetime.utcfromtimestamp(t).weekday())]
        for a in A:
            f += list(cot_at(a, d))
        nx = s[i+1]
        X.append(f); yd.append(1 if nx[4] > nx[1] else 0)
        ym.append((nx[2]-nx[3])/nx[1]); T.append(t)
    return np.array(X, float), np.array(yd), np.array(ym), np.array(T)

MODELS = {
    'logistic': lambda: LogisticRegression(max_iter=1000, C=0.1),
    'rf':       lambda: RandomForestClassifier(n_estimators=120, max_depth=5,
                                               min_samples_leaf=20,
                                               random_state=0, n_jobs=-1),
    'gb':       lambda: GradientBoostingClassifier(n_estimators=80, max_depth=3,
                                                   learning_rate=0.05,
                                                   subsample=0.8,
                                                   random_state=0),
}

say("\n" + "=" * 78)
say("DIRECTION: ALL NINE LAYERS COMBINED, WALK-FORWARD (refit every 5 bars)")
say("=" * 78)

store = {}
for a in A:
    X, yd, ym, T = build(a)
    say(f"\n--- {a.upper()}  samples={len(X)}  features={X.shape[1]}")
    preds = {k: [] for k in MODELS}; truth = []; times = []
    fitted = {}
    for i in range(150, len(X)):
        if (i - 150) % 5 == 0:                   # refit every 5 bars
            sc = StandardScaler().fit(X[:i])
            Xs = sc.transform(X[:i])
            if len(np.unique(yd[:i])) < 2:
                continue
            fitted = {k: m().fit(Xs, yd[:i]) for k, m in MODELS.items()}
            cur_sc = sc
        if not fitted:
            continue
        xs = cur_sc.transform(X[i:i+1])
        for k, m in fitted.items():
            preds[k].append(float(m.predict_proba(xs)[0, 1]))
        truth.append(yd[i]); times.append(T[i])
    truth = np.array(truth)
    for k in MODELS:
        pr = np.array(preds[k])
        acc = np.mean((pr > .5).astype(int) == truth)*100
        n = len(truth); z = (acc-50)/(np.sqrt(.25/n)*100)
        say(f"    {k:9s} OOS acc {acc:5.2f}%   z vs 50% = {z:+5.2f}   n={n}")
        store[(a, k)] = (pr, truth)
    pe = np.mean([np.array(preds[k]) for k in MODELS], axis=0)
    acc = np.mean((pe > .5).astype(int) == truth)*100
    n = len(truth); z = (acc-50)/(np.sqrt(.25/n)*100)
    say(f"    {'ENSEMBLE':9s} OOS acc {acc:5.2f}%   z vs 50% = {z:+5.2f}   n={n}")
    store[(a, 'ens')] = (pe, truth)

say("\n" + "=" * 78)
say("CONFIDENCE FILTER -- where >80% would have to come from")
say("=" * 78)
say("A real combination should get much more accurate when it is confident.")
for a in A:
    say(f"\n  {a.upper()}")
    for k in list(MODELS) + ['ens']:
        pr, truth = store[(a, k)]
        conf = np.abs(pr - .5); line = f"    {k:9s}"
        for q in (0.0, .5, .8, .9, .95):
            m = conf >= np.quantile(conf, q)
            if m.sum() < 5:
                line += f"  top{int((1-q)*100):>3d}%: n/a"; continue
            aa = np.mean((pr[m] > .5).astype(int) == truth[m])*100
            line += f"  top{int((1-q)*100):>3d}%:{aa:5.1f}%(n={m.sum():3d})"
        say(line)

say("\n" + "=" * 78)
say("MAGNITUDE, same combined features (the control that has always worked)")
say("=" * 78)
for a in A:
    X, yd, ym, T = build(a)
    pred, act = [], []
    for i in range(150, len(X)):
        if (i - 150) % 5 == 0:
            sc = StandardScaler().fit(X[:i])
            m = RandomForestRegressor(n_estimators=120, max_depth=6,
                                      min_samples_leaf=15, random_state=0,
                                      n_jobs=-1).fit(sc.transform(X[:i]), ym[:i])
        pred.append(float(m.predict(sc.transform(X[i:i+1]))[0]))
        act.append(ym[i])
    pred, act = np.array(pred), np.array(act)
    ic = np.corrcoef(pred, act)[0, 1]; n = len(pred)
    t = ic*np.sqrt(n-2)/np.sqrt(1-ic**2)
    say(f"  {a:5s} next-bar RANGE  IC={ic:+.4f}  t={t:+6.2f}  "
        f"R2={ic**2*100:5.1f}%  n={n}")
