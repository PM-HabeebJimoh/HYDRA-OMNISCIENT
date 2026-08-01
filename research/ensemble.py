"""
THE COMBINATION MODEL.

Fair criticism: I tested 34 signals ONE AT A TIME. A signal can be individually
worthless (t~0) and still be valuable inside a combination -- interactions,
conditioning, nonlinearity. Never properly tested. Doing it now.

Every layer this project has gathered, in one feature matrix:
  L1 price/return structure          (Investing.com 1H/4H/daily OHLC)
  L2 bar microstructure, 32 feats    (CLV, wicks, gaps, dispersion, vol-of-vol)
  L3 macro levels                    (FRED: VIX DXY HYSPREAD CURVE GVZ VIX3M)
  L4 macro changes/momentum          (same, differenced)
  L5 implied vol + VRP               (GVZ vs realised)
  L6 cross-market ratios             (GVZ/VIX, VIX3M/VIX, HY/VIX ...)
  L7 economic calendar SCHEDULE      (known days ahead)
  L8 calendar surprise + ex-ante     (forecast-prev, actual-forecast)
  L9 CFTC positioning                (spec net, percentile, flow, commercials)

Models: logistic, ridge, random forest, gradient boosting, and a stacked
ensemble -- all with STRICTLY WALK-FORWARD fitting (train on past only).

Two targets:
  DIRECTION  sign of next-bar return
  MAGNITUDE  next-bar range (the thing that has always worked)

Everything real. No synthetic data.
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

from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# ------------------------------------------------------------------ data
p1h = load_1h()
p4 = resample_4h(p1h)
b4 = sorted(p4)
print(f"4H bars: {len(b4)}  "
      f"{dt.datetime.utcfromtimestamp(b4[0]):%Y-%m-%d} .. "
      f"{dt.datetime.utcfromtimestamp(b4[-1]):%Y-%m-%d}")

MAC = {}
for f in glob.glob(str(ROOT / 'data/raw/macro/*.json')):
    d = json.load(open(f))
    nm = Path(f).stem
    MAC[nm] = {dt.date.fromisoformat(x): v
               for x, v in zip(d['dates'], d['v']) if v is not None}
print("macro series:", ", ".join(sorted(MAC)))

EVENTS = build_events()
sched4 = collections.Counter(e['ts'] - (e['ts'] % 14400) for e in EVENTS)
surp4, exante4 = {}, {}
for e in EVENTS:
    k = e['ts'] - (e['ts'] % 14400)
    if e.get('surp_z') is not None:
        surp4[k] = surp4.get(k, 0) + np.clip(e['surp_z'], -3, 3)
    if e.get('exante') is not None:
        exante4[k] = exante4.get(k, 0) + np.sign(e['exante'])

COT = json.load(open(ROOT / 'data/raw/cot/cot_3assets.json'))
cot = {}
for a in A:
    rows = COT[a]
    hist = []
    for k, (ds, nl, ns, cl, cs, oi) in enumerate(rows):
        asof = dt.date.fromisoformat(ds)
        pub = asof + dt.timedelta(days=3)      # published Friday, honest lag
        net = nl - ns
        pct = float(np.mean([h < net for h in hist])) if len(hist) >= 12 else 0.5
        dnet = (net - (rows[k-1][1] - rows[k-1][2])) if k else 0.0
        cot.setdefault(a, []).append(
            dict(pub=pub, net=net, pct=pct, dnet=dnet,
                 cnet=cl - cs, net_oi=net / oi))
        hist.append(net)

def cot_at(a, d):
    """Most recent COT row PUBLISHED strictly before date d."""
    best = None
    for r in cot[a]:
        if r['pub'] < d:
            best = r
        else:
            break
    return best

def macro_at(nm, d, lag=1):
    """Most recent macro obs at least `lag` days before d (publication lag)."""
    cut = d - dt.timedelta(days=lag)
    best = None
    for k in sorted(MAC.get(nm, {})):
        if k <= cut:
            best = MAC[nm][k]
        else:
            break
    return best

# ------------------------------------------------------------ features
def series(a):
    out, pc = [], None
    for t in b4:
        x = p4[t][a]
        out.append(dict(t=t, o=x['open'], h=x['high'], l=x['low'], c=x['close'],
                        pc=pc if pc else x['open']))
        pc = x['close']
    return out

S = {a: series(a) for a in A}

def build(target_asset):
    s = S[target_asset]
    X, yd, ym, T = [], [], [], []
    for i in range(60, len(s) - 1):
        f, nm = [], []
        d = dt.datetime.utcfromtimestamp(s[i]['t']).date()

        # ---- L1/L2  price + microstructure, per asset (strictly past)
        for a in A:
            q = S[a]
            b = q[i]
            rng = max(b['h'] - b['l'], 1e-12)
            f += [(b['c'] - b['o']) / b['o'],                    # body
                  (b['c'] - b['l']) / rng,                       # CLV
                  (b['h'] - max(b['o'], b['c'])) / rng,          # upper wick
                  (min(b['o'], b['c']) - b['l']) / rng,          # lower wick
                  abs(b['c'] - b['o']) / rng,                    # body/range
                  (b['o'] - q[i-1]['c']) / q[i-1]['c'],          # gap
                  rng / b['o']]                                  # range
            nm += [f'{a}_body', f'{a}_clv', f'{a}_uw', f'{a}_lw',
                   f'{a}_br', f'{a}_gap', f'{a}_rng']
            r = [(q[j]['c'] - q[j]['o']) / q[j]['o'] for j in range(i-20, i+1)]
            rr = [(q[j]['h'] - q[j]['l']) / q[j]['o'] for j in range(i-20, i+1)]
            f += [np.mean(r[-3:]), np.mean(r[-10:]), np.std(r[-10:]),
                  np.mean(rr[-5:]), np.mean(rr[-20:]),
                  np.std(rr[-10:]),
                  np.mean(rr[-5:]) / (np.mean(rr[-20:]) + 1e-12),
                  float(np.sum(np.sign(r[-5:]))),                # streak
                  ]
            nm += [f'{a}_m3', f'{a}_m10', f'{a}_v10', f'{a}_rr5',
                   f'{a}_rr20', f'{a}_vov', f'{a}_rratio', f'{a}_streak']

        # ---- cross-asset dispersion / alignment (the original Agba idea)
        bodies = [(S[a][i]['c'] - S[a][i]['o']) / S[a][i]['o'] for a in A]
        f += [float(np.std(bodies)), float(np.mean(bodies)),
              float(np.sum(np.sign(bodies))),
              float(abs(np.sum(np.sign(bodies))) == 3)]
        nm += ['disp', 'meanbody', 'align_sum', 'aligned3']

        # ---- L3/L4/L5/L6  macro levels, changes, ratios (lagged 1 day)
        lv = {}
        for k in ('VIX', 'DXY', 'HYSPREAD', 'CURVE', 'GVZ', 'VIX3M'):
            v = macro_at(k, d)
            lv[k] = v
            f.append(v if v is not None else 0.0)
            nm.append(f'lv_{k}')
        for k in ('VIX', 'DXY', 'HYSPREAD', 'CURVE', 'GVZ', 'VIX3M'):
            a5 = macro_at(k, d, 6)
            f.append((lv[k] - a5) / (abs(a5) + 1e-9)
                     if (lv[k] is not None and a5) else 0.0)
            nm.append(f'ch_{k}')
        g, v_, v3, hy = lv['GVZ'], lv['VIX'], lv['VIX3M'], lv['HYSPREAD']
        f += [g / v_ if (g and v_) else 0.0,
              v3 / v_ if (v3 and v_) else 0.0,
              hy / v_ if (hy and v_) else 0.0]
        nm += ['GVZ_VIX', 'VIX3M_VIX', 'HY_VIX']
        # VRP: implied (GVZ) vs realised gold vol
        rg = [(S['gold'][j]['c'] - S['gold'][j]['o']) / S['gold'][j]['o']
              for j in range(i-20, i+1)]
        rv = float(np.std(rg)) * np.sqrt(6 * 252) * 100
        f += [rv, (g - rv) if g else 0.0]
        nm += ['realvol', 'vrp']

        # ---- L7/L8  calendar (schedule known days ahead; surprise at release)
        t = s[i]['t']
        f += [float(sched4.get(t, 0)),
              float(sched4.get(t + 14400, 0)),      # NEXT bar's schedule!
              float(surp4.get(t, 0.0)),
              float(exante4.get(t + 14400, 0.0)),
              float(dt.datetime.utcfromtimestamp(t).hour),
              float(dt.datetime.utcfromtimestamp(t).weekday())]
        nm += ['sched_now', 'sched_next', 'surp_now', 'exante_next',
               'hour', 'dow']

        # ---- L9  positioning (published Friday, lagged honestly)
        for a in A:
            c = cot_at(a, d)
            if c:
                f += [c['pct'], c['net_oi'], np.sign(c['dnet']),
                      np.sign(c['cnet'])]
            else:
                f += [0.5, 0.0, 0.0, 0.0]
            nm += [f'{a}_cotpct', f'{a}_cotoi', f'{a}_cotflow', f'{a}_cotcomm']

        nxt = s[i+1]
        X.append(f)
        yd.append(1 if nxt['c'] > nxt['o'] else 0)
        ym.append((nxt['h'] - nxt['l']) / nxt['o'])
        T.append(s[i]['t'])
    return np.array(X, float), np.array(yd), np.array(ym), np.array(T), nm

# ------------------------------------------------------------ walk-forward
def walkforward(X, y, T, kind='clf', min_train=150, step=1):
    """Expanding-window: fit on [0,i), predict i. Never sees the future."""
    preds, truth, times = [], [], []
    models = dict(
        logistic=lambda: LogisticRegression(max_iter=2000, C=0.1),
        rf=lambda: RandomForestClassifier(n_estimators=300, max_depth=5,
                                          min_samples_leaf=20, random_state=0,
                                          n_jobs=-1),
        gb=lambda: GradientBoostingClassifier(n_estimators=150, max_depth=3,
                                              learning_rate=0.03,
                                              subsample=0.8, random_state=0),
    )
    out = {k: [] for k in models}
    for i in range(min_train, len(X), step):
        Xtr, ytr = X[:i], y[:i]
        if len(np.unique(ytr)) < 2:
            continue
        sc = StandardScaler().fit(Xtr)
        Xs, xs = sc.transform(Xtr), sc.transform(X[i:i+1])
        for k, mk in models.items():
            m = mk().fit(Xs, ytr)
            out[k].append(float(m.predict_proba(xs)[0, 1]))
        truth.append(y[i]); times.append(T[i])
    return out, np.array(truth), np.array(times)

print()
print("=" * 78)
print("DIRECTION: EVERY LAYER COMBINED, WALK-FORWARD (never sees the future)")
print("=" * 78)

allres = {}
for a in A:
    X, yd, ym, T, nm = build(a)
    print(f"\n--- {a.upper()}   samples={len(X)}  features={X.shape[1]}")
    out, truth, times = walkforward(X, yd, T)
    for k, pr in out.items():
        pr = np.array(pr)
        acc = np.mean((pr > 0.5).astype(int) == truth) * 100
        # t-stat of the directional bet
        bet = np.where(pr > 0.5, 1, -1)
        base = max(np.mean(truth), 1 - np.mean(truth)) * 100
        n = len(truth)
        se = np.sqrt(0.25 / n) * 100
        z = (acc - 50) / se
        print(f"    {k:9s} OOS acc {acc:5.2f}%   (majority-class {base:.2f}%)   "
              f"z vs 50% = {z:+.2f}   n={n}")
        allres[(a, k)] = (acc, z, n, pr, truth, times)

print()
print("=" * 78)
print("CONFIDENCE FILTER: does accuracy rise when the ensemble is SURE?")
print("=" * 78)
print("If a combination model has real signal, its high-confidence subset")
print("should be much more accurate. This is where >80% would have to come from.")
for a in A:
    print(f"\n  {a.upper()}")
    for k in ('logistic', 'rf', 'gb'):
        acc, z, n, pr, truth, times = allres[(a, k)]
        conf = np.abs(pr - 0.5)
        line = f"    {k:9s} "
        for q in (0.0, 0.5, 0.8, 0.9, 0.95):
            thr = np.quantile(conf, q)
            m = conf >= thr
            if m.sum() < 5:
                line += f"  top{int((1-q)*100):>3d}%:  n/a"
                continue
            aa = np.mean((pr[m] > 0.5).astype(int) == truth[m]) * 100
            line += f"  top{int((1-q)*100):>3d}%:{aa:5.1f}%(n={m.sum()})"
        print(line)

print()
print("=" * 78)
print("MAGNITUDE with the same combined feature set (the control)")
print("=" * 78)
for a in A:
    X, yd, ym, T, nm = build(a)
    pred, act = [], []
    for i in range(150, len(X)):
        sc = StandardScaler().fit(X[:i])
        m = RandomForestRegressor(n_estimators=200, max_depth=6,
                                  min_samples_leaf=15, random_state=0,
                                  n_jobs=-1).fit(sc.transform(X[:i]), ym[:i])
        pred.append(float(m.predict(sc.transform(X[i:i+1]))[0]))
        act.append(ym[i])
    pred, act = np.array(pred), np.array(act)
    ic = np.corrcoef(pred, act)[0, 1]
    n = len(pred)
    t = ic * np.sqrt(n - 2) / np.sqrt(1 - ic**2)
    print(f"  {a:5s} next-bar RANGE   IC = {ic:+.4f}   t = {t:+.2f}   "
          f"R2 = {ic**2*100:.1f}%   n={n}")
