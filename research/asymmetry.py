"""
THE COMBINATION I NEVER TESTED.

Your question 1 was right and it exposed my blind spot. Working it through:

  * At 80% accuracy, leverage delivers absurd ROI. Leverage was never the issue.
  * 500%/month needs only 58.3% accuracy at 1:1 -- NOT 80%.
  * My measured best is 53.4%. Gap = 4.9 points.
  * BUT accuracy is only one of TWO levers. The other is PAYOFF RATIO.
  * At my ALREADY-MEASURED 53.4%, a payoff of just 1.22:1 gives 500%/month.

And payoff ratio is a function of stop/target placement, which depends on
the RANGE of the bar -- the one quantity I can forecast (IC 0.50, t=+17).

So: use the weak direction signal for SIDE, and the strong magnitude signal
for STOP/TARGET GEOMETRY. That is the untested cell.

Honest construction throughout:
  * direction from a walk-forward ensemble (never sees the future)
  * range forecast from a walk-forward regressor (never sees the future)
  * intrabar path resolved on 1H sub-bars, not 4H OHLC guesses
  * if both stop and target are hit in the same 1H bar, count it as a LOSS
  * real spreads charged on entry and exit
  * full decomposition of every branch
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
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def say(*a): print(*a, flush=True)

SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}
p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4); b1 = sorted(p1h)
SUB = collections.defaultdict(list)
for t in b1:
    SUB[t - (t % 14400)].append(t)

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
N = len(b4)

def feats(a, i):
    q = S[a]; _, o, h, l, c, pc = q[i]; rng = max(h - l, 1e-12)
    r = [(q[j][4]-q[j][1])/q[j][1] for j in range(i-20, i+1)]
    rr = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
    return [(c-o)/o, (c-l)/rng, (h-max(o,c))/rng, (min(o,c)-l)/rng,
            abs(c-o)/rng, (o-q[i-1][4])/q[i-1][4], rng/o,
            np.mean(r[-3:]), np.mean(r[-10:]), np.std(r[-10:]),
            np.mean(rr[-3:]), np.mean(rr[-5:]), np.mean(rr[-20:]),
            np.std(rr[-10:]), np.mean(rr[-3:])/(np.mean(rr[-20:])+1e-12),
            float(np.sum(np.sign(r[-5:]))), np.mean(np.abs(r[-5:]))]

def ctx(i):
    t = b4[i]; d = dt.datetime.utcfromtimestamp(t).date(); f = []
    for k in MKEYS:
        v = macro_at(k, d); f.append(v if v is not None else 0.0)
    f += [float(sched4.get(t, 0)), float(sched4.get(t+14400, 0)),
          float(dt.datetime.utcfromtimestamp(t).hour),
          float(dt.datetime.utcfromtimestamp(t).weekday())]
    return f

def build(a):
    X, ydir, yrng, idx = [], [], [], []
    q = S[a]
    for i in range(60, N-1):
        X.append(feats(a, i) + [f for b in A if b != a for f in feats(b, i)[:7]] + ctx(i))
        nx = q[i+1]
        ydir.append(1 if nx[4] > nx[1] else 0)
        yrng.append((nx[2]-nx[3])/nx[1])
        idx.append(i)
    return np.array(X, float), np.array(ydir), np.array(yrng), np.array(idx)

def trade(a, i, side, stop_f, targ_f):
    """Walk 1H sub-bars in order. stop_f/targ_f are fractions of price.
    If both hit inside the SAME 1H bar, book a LOSS (worst case)."""
    tb = S[a][i+1][0]
    subs = SUB.get(tb, [])
    if len(subs) < 2:
        return None
    o = p1h[subs[0]][a]['open']; hs = SPREAD[a]
    if side > 0:
        tp, sl = o*(1+targ_f), o*(1-stop_f)
    else:
        tp, sl = o*(1-targ_f), o*(1+stop_f)
    for t in subs:
        b = p1h[t][a]
        hit_tp = (b['high'] >= tp) if side > 0 else (b['low'] <= tp)
        hit_sl = (b['low'] <= sl) if side > 0 else (b['high'] >= sl)
        if hit_tp and hit_sl:
            return -stop_f - 2*hs                       # worst case
        if hit_sl:
            return -stop_f - 2*hs
        if hit_tp:
            return targ_f - 2*hs
    c = p1h[subs[-1]][a]['close']
    return side*(c-o)/o - 2*hs                          # time exit

say("="*78)
say("WALK-FORWARD: direction model + range model, then asymmetric geometry")
say("="*78)

RES = {}
for a in A:
    X, yd, yr, idx = build(a)
    pd_, pr_, tr_, ix_ = [], [], [], []
    dm = rm = sc = None
    for k in range(150, len(X)):
        if (k-150) % 10 == 0:
            if len(np.unique(yd[:k])) < 2: continue
            sc = StandardScaler().fit(X[:k])
            Xs = sc.transform(X[:k])
            dm = RandomForestClassifier(n_estimators=150, max_depth=5,
                    min_samples_leaf=20, random_state=0, n_jobs=-1).fit(Xs, yd[:k])
            rm = RandomForestRegressor(n_estimators=150, max_depth=6,
                    min_samples_leaf=15, random_state=0, n_jobs=-1).fit(Xs, yr[:k])
        if dm is None: continue
        xs = sc.transform(X[k:k+1])
        pd_.append(float(dm.predict_proba(xs)[0, 1]))
        pr_.append(float(rm.predict(xs)[0]))
        tr_.append(yd[k]); ix_.append(idx[k])
    pd_, pr_, tr_, ix_ = map(np.array, (pd_, pr_, tr_, ix_))
    acc = np.mean((pd_ > .5).astype(int) == tr_)*100
    RES[a] = (pd_, pr_, tr_, ix_)
    say(f"  {a:5s} direction acc {acc:5.2f}%   range IC "
        f"{np.corrcoef(pr_, [ (S[a][i+1][2]-S[a][i+1][3])/S[a][i+1][1] for i in ix_])[0,1]:+.3f}"
        f"   n={len(tr_)}")

say()
say("="*78)
say("THE ASYMMETRY GRID: does a wider target actually pay?")
say("="*78)
say("stop and target set as fractions of the FORECAST range.")
say(f"{'stop':>6s} {'targ':>6s} {'asset':>6s} {'n':>5s} {'WR%':>6s} "
    f"{'mean%':>9s} {'t':>7s} {'realised b':>11s}")
grid = []
for stop_m, targ_m in [(0.5,0.5),(0.5,0.75),(0.5,1.0),(0.5,1.5),
                       (0.75,0.75),(0.75,1.5),(1.0,1.0),(1.0,2.0)]:
    for a in A:
        pd_, pr_, tr_, ix_ = RES[a]
        pnl = []
        for k, i in enumerate(ix_):
            side = 1 if pd_[k] > .5 else -1
            rf = max(pr_[k], 1e-5)
            v = trade(a, i, side, stop_m*rf, targ_m*rf)
            if v is not None: pnl.append(v)
        if len(pnl) < 30: continue
        m, t, n = tstat(pnl)
        w = [x for x in pnl if x > 0]; L = [x for x in pnl if x <= 0]
        b = abs(np.mean(w)/np.mean(L)) if w and L else float('nan')
        wr = len(w)/n*100
        say(f"{stop_m:6.2f} {targ_m:6.2f} {a:>6s} {n:5d} {wr:6.1f} "
            f"{m*100:+9.4f} {t:+7.2f} {b:11.2f}")
        grid.append((t, stop_m, targ_m, a, n, wr, m, b, pnl))

say()
say("="*78)
say("BEST CELL AND WHAT IT IMPLIES")
say("="*78)
grid.sort(reverse=True, key=lambda x: x[0])
for g in grid[:5]:
    t, sm, tm, a, n, wr, m, b, pnl = g
    say(f"  {a} stop{sm} targ{tm}: WR {wr:.1f}%  b={b:.2f}  mean {m*100:+.4f}%  "
        f"t={t:+.2f}  sign-flip p={signflip_null(pnl):.4f}")
say(f"\n  cells searched: {len(grid)}  expected max|t| ~ "
    f"{np.sqrt(2*np.log(max(len(grid),2))):.2f}")

say()
say("="*78)
say("KELLY ON THE BEST CELL -- the arithmetic you asked for")
say("="*78)
if grid:
    t, sm, tm, a, n, wr, m, b, pnl = grid[0]
    p = wr/100
    f = (p*b - (1-p))/b if b > 0 else 0
    say(f"  measured p={p:.4f}  b={b:.2f}  Kelly f*={f:+.4f}")
    if f > 0:
        g = p*np.log(1+f*b) + (1-p)*np.log(1-f)
        say(f"  growth/trade {g:+.5f}  -> monthly (130 trades) "
            f"{(np.exp(g*130)-1)*100:,.1f}%")
    else:
        say("  f* <= 0 : NEGATIVE EDGE. No leverage can help.")
    say(f"  mean per trade is {m*100:+.4f}% -- this is the ground truth,")
    say(f"  and it already includes spreads and worst-case whipsaw.")
