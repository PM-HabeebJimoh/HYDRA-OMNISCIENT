"""
REPLACEMENT MINDSET: four framings I have never tested.

Everything so far asked ONE question in ONE frame:
    "will XAUUSD go up in USD terms next bar?"
That question is unpredictable (0/34). But it is not the only question, and
I have been treating it as if it were. Four replacements:

  R1  CROSS-SECTIONAL, not time-series.
      Don't ask "will gold rise". Ask "will gold beat AUD".
      All three assets are quoted vs USD, so they share one huge common
      factor: the dollar. That factor is what is unpredictable. A dollar-
      NEUTRAL long/short kills it by construction and asks only about the
      residual. Cross-sectional prediction is a different problem with a
      different (much better) academic track record than time-series.

  R2  INVERT THE MAGNITUDE TRADE.
      My magnitude model is 74-79% accurate but LOSES money bought as a
      straddle, because bracket width scales with the forecast so signal
      and hurdle cancel. That cancellation is a property of BUYING range.
      If I SELL range on predicted-quiet bars, the same scaling works FOR
      me. I have run the buy side ~20 times and never once run the mirror.

  R3  PATH, not endpoint.
      "Which gets touched first, +X or -X?" is a different random variable
      from "where does it close". Barrier order carries information that
      close-open destroys.

  R4  ASYMMETRY, not mean.
      If I cannot predict the mean but CAN predict the skew, a payoff that
      is convex in the right tail still makes money with zero directional
      accuracy.

All real Investing.com/FRED/CFTC data. Walk-forward. Worst-case costs.
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
SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}

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
    """Causal features for asset a at bar i."""
    q = S[a]; _, o, h, l, c, pc = q[i]
    rng = max(h - l, 1e-12)
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

def wf_clf(X, y, min_tr=150, refit=10, **kw):
    pr, tr, idx = [], [], []
    mdl = sc = None
    for i in range(min_tr, len(X)):
        if (i-min_tr) % refit == 0:
            if len(np.unique(y[:i])) < 2: continue
            sc = StandardScaler().fit(X[:i])
            mdl = RandomForestClassifier(n_estimators=100, max_depth=5,
                                         min_samples_leaf=20, random_state=0,
                                         n_jobs=-1, **kw).fit(sc.transform(X[:i]), y[:i])
        if mdl is None: continue
        pr.append(float(mdl.predict_proba(sc.transform(X[i:i+1]))[0, 1]))
        tr.append(y[i]); idx.append(i)
    return np.array(pr), np.array(tr), np.array(idx)

# =====================================================================
say("="*78)
say("R1  CROSS-SECTIONAL DIRECTION  (dollar-neutral: does the common")
say("    USD factor hide a predictable residual?)")
say("="*78)
say("Pairs are gold/eur, gold/aud, eur/aud. Target = will X outperform Y.")
say("A long/short pair has NO net dollar exposure by construction.\n")

PAIRS = [('gold','eur'), ('gold','aud'), ('eur','aud')]
xs_store = {}
for x, y_ in PAIRS:
    X, Y, RET = [], [], []
    for i in range(60, N-1):
        f = feats(x, i) + feats(y_, i) + ctx(i)
        # relative past performance = the cross-sectional momentum term
        rx = [(S[x][j][4]-S[x][j][1])/S[x][j][1] for j in range(i-20, i+1)]
        ry = [(S[y_][j][4]-S[y_][j][1])/S[y_][j][1] for j in range(i-20, i+1)]
        f += [np.mean(rx[-3:])-np.mean(ry[-3:]),
              np.mean(rx[-10:])-np.mean(ry[-10:]),
              np.sum(rx[-20:])-np.sum(ry[-20:])]
        nx, ny = S[x][i+1], S[y_][i+1]
        rrx = (nx[4]-nx[1])/nx[1]; rry = (ny[4]-ny[1])/ny[1]
        X.append(f); Y.append(1 if rrx > rry else 0); RET.append(rrx-rry)
    X = np.array(X, float); Y = np.array(Y); RET = np.array(RET)
    pr, tr, idx = wf_clf(X, Y)
    acc = np.mean((pr > .5).astype(int) == tr)*100
    n = len(tr); z = (acc-50)/(np.sqrt(.25/n)*100)
    conf = np.abs(pr-.5)
    line = f"  {x}/{y_:5s} acc {acc:5.2f}%  z={z:+5.2f}  n={n}"
    for q in (.8, .9):
        m = conf >= np.quantile(conf, q)
        line += f"   top{int((1-q)*100)}%:{np.mean((pr[m]>.5).astype(int)==tr[m])*100:5.1f}%"
    say(line)
    # money: trade the spread, both legs, real costs
    cost = 2*(SPREAD[x]+SPREAD[y_])
    sig = np.where(pr > .5, 1, -1)
    pnl = sig*RET[idx] - cost
    m, t, nn = tstat(list(pnl))
    say(f"           spread PnL mean {m*100:+.4f}%  t={t:+5.2f}  "
        f"WR {np.mean(pnl>0)*100:.1f}%  (costs {cost*100:.4f}%)")
    xs_store[(x,y_)] = (pr, tr, idx, RET)

# =====================================================================
say()
say("="*78)
say("R2  INVERT THE MAGNITUDE TRADE  (sell range on predicted-QUIET bars)")
say("="*78)
say("Buying range fails because the bracket scales with the forecast.")
say("Selling range on quiet bars: that scaling now works in my favour.")
say("Short straddle = fade both extremes, capped by a stop at k*ATR.\n")
say(f"{'asset':6s} {'bucket':22s} {'n':>5s} {'mean%':>9s} {'t':>7s} {'WR%':>6s}")

for a in A:
    X, RNG, MED = [], [], []
    for i in range(60, N-1):
        X.append(feats(a, i) + ctx(i))
        q = S[a]; nx = q[i+1]
        hist = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
        RNG.append((nx[2]-nx[3])/nx[1]); MED.append(float(np.median(hist)))
    X = np.array(X, float); RNG = np.array(RNG); MED = np.array(MED)
    yq = (RNG < MED).astype(int)          # 1 = QUIET bar
    pr, tr, idx = wf_clf(X, yq)
    acc = np.mean((pr > .5).astype(int) == tr)*100
    say(f"  {a:5s} quiet-bar accuracy {acc:.2f}%  (50/50 question)")
    q = S[a]
    for thr_q, lab in [(0.0,'ALL bars'), (.5,'top 50% quiet'),
                       (.8,'top 20% quiet'), (.9,'top 10% quiet')]:
        thr = np.quantile(pr, thr_q)
        pnl = []
        for k, i in enumerate(idx):
            if pr[k] < thr: continue
            hist = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
            w = float(np.mean(hist))              # fade band
            stop = 2.0*w                          # stop at 2x band
            _, o, h, l, c, _ = q[i+1]
            hs = SPREAD[a]
            up, dn = o*(1+w), o*(1-w)
            su, sd = o*(1+stop), o*(1-stop)
            hit_u, hit_d = h >= up, l <= dn
            stop_u, stop_d = h >= su, l <= sd
            if stop_u and stop_d:  v = -2*stop - 2*hs   # worst case both stops
            elif stop_u:           v = -stop - hs
            elif stop_d:           v = -stop - hs
            elif hit_u and hit_d:  v = 2*w - 2*hs       # faded both, kept band
            elif hit_u:            v = (up-c)/o - hs
            elif hit_d:            v = (c-dn)/o - hs
            else:                  v = abs(c-o)/o - hs  # never reached band
            pnl.append(v)
        if len(pnl) < 10: continue
        m, t, nn = tstat(pnl)
        say(f"        {lab:22s} {nn:5d} {m*100:+9.4f} {t:+7.2f} "
            f"{np.mean([x>0 for x in pnl])*100:6.1f}")

# =====================================================================
say()
say("="*78)
say("R3  PATH ORDER  (which barrier is touched FIRST -- not where it closes)")
say("="*78)
for a in A:
    X, Y = [], []
    q = S[a]
    for i in range(60, N-1):
        hist = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)]
        w = float(np.mean(hist))*0.5
        _, o, h, l, c, _ = q[i+1]
        hu, hd = h >= o*(1+w), l <= o*(1-w)
        if hu == hd:                       # both or neither -> undefined
            continue
        X.append(feats(a, i) + ctx(i)); Y.append(1 if hu else 0)
    X = np.array(X, float); Y = np.array(Y)
    if len(X) < 250: 
        say(f"  {a:5s} too few clean cases ({len(X)})"); continue
    pr, tr, idx = wf_clf(X, Y)
    acc = np.mean((pr > .5).astype(int) == tr)*100
    n = len(tr); z = (acc-50)/(np.sqrt(.25/n)*100)
    conf = np.abs(pr-.5)
    m = conf >= np.quantile(conf, .9)
    say(f"  {a:5s} up-first accuracy {acc:5.2f}%  z={z:+5.2f}  n={n}   "
        f"top10%:{np.mean((pr[m]>.5).astype(int)==tr[m])*100:5.1f}%")

# =====================================================================
say()
say("="*78)
say("R4  SKEW  (can I predict asymmetry even with no directional mean?)")
say("="*78)
say("Target: is the upper wick bigger than the lower wick next bar?")
say("If yes, a convex right-tail payoff profits at 50% directional accuracy.\n")
for a in A:
    X, Y, ASY = [], [], []
    q = S[a]
    for i in range(60, N-1):
        _, o, h, l, c, _ = q[i+1]
        up_w, dn_w = h - max(o, c), min(o, c) - l
        X.append(feats(a, i) + ctx(i))
        Y.append(1 if up_w > dn_w else 0)
        ASY.append((up_w - dn_w)/o)
    X = np.array(X, float); Y = np.array(Y); ASY = np.array(ASY)
    pr, tr, idx = wf_clf(X, Y)
    acc = np.mean((pr > .5).astype(int) == tr)*100
    n = len(tr); z = (acc-50)/(np.sqrt(.25/n)*100)
    sig = np.where(pr > .5, 1, -1)
    m_, t_, _ = tstat(list(sig*ASY[idx] - 2*SPREAD[a]))
    say(f"  {a:5s} skew-sign accuracy {acc:5.2f}%  z={z:+5.2f}  n={n}   "
        f"traded asym mean {m_*100:+.4f}%  t={t_:+5.2f}")
