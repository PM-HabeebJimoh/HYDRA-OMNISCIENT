"""
JULY 2026 OUT-OF-SAMPLE BACKTEST OF THE XAUUSD RANGE PREDICTOR.

Protocol, strictly enforced:
  * The model is trained ONLY on data before each prediction.
  * For every July 2026 bar, the training set ends at that bar.
  * The confidence threshold is FROZEN from pre-July data only --
    it is NOT re-derived on July, which would be look-ahead.
  * Every July prediction is then scored.

Claimed: 86.84% at top-5% confidence.
This tests that claim on one held-out month.
"""
import json, glob, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, str(ROOT/'research'))
from xau_range_predictor import (load_bars, features, trailing_median_range,
                                 fit_predict, LOOKBACK, MIN_TRAIN)
def say(*a): print(*a, flush=True)

ts, bars = load_bars()
say("="*74)
say("JULY 2026 BACKTEST -- XAUUSD 1H RANGE PREDICTOR")
say("="*74)
say(f"full dataset: {len(bars)} bars  "
    f"{dt.datetime.utcfromtimestamp(ts[0]):%Y-%m-%d} .. "
    f"{dt.datetime.utcfromtimestamp(ts[-1]):%Y-%m-%d}")

# build the full feature/label panel
X, lab, med, keep = [], [], [], []
for i in range(LOOKBACK+4, len(bars)-1):
    X.append(features(bars, i, ts))
    m = trailing_median_range(bars, i)
    nx = bars[i+1]
    med.append(m)
    lab.append(1 if (nx[1]-nx[2])/nx[0] > m else 0)
    keep.append(i)
X = np.array(X); lab = np.array(lab, float); keep = np.array(keep)
month = np.array([dt.datetime.utcfromtimestamp(ts[i]).strftime('%Y-%m')
                  for i in keep])

is_july = month == '2026-07'
pre_july = ~is_july & (keep < keep[is_july][0])
say(f"pre-July training pool : {pre_july.sum()} bars")
say(f"July 2026 test bars    : {is_july.sum()} bars")
say(f"July range: "
    f"{dt.datetime.utcfromtimestamp(ts[keep[is_july][0]]):%Y-%m-%d %H:%M} .. "
    f"{dt.datetime.utcfromtimestamp(ts[keep[is_july][-1]]):%Y-%m-%d %H:%M}")

# ---- STEP 1: freeze the threshold using ONLY pre-July data
say()
say("="*74)
say("STEP 1: FREEZE THE CONFIDENCE THRESHOLD ON PRE-JULY DATA ONLY")
say("="*74)
pre_idx = np.where(pre_july)[0]
pre_pred = []
for k in pre_idx:
    if k < MIN_TRAIN:
        pre_pred.append(np.nan); continue
    pre_pred.append(fit_predict(X[:k], lab[:k], X[k]))
pre_pred = np.array(pre_pred)
ok = ~np.isnan(pre_pred)
pre_conf = np.abs(pre_pred[ok]-0.5)
THR = float(np.quantile(pre_conf, 0.95))
pre_act = lab[pre_idx][ok].astype(int)
m = pre_conf >= THR
say(f"  pre-July predictions: {ok.sum()}")
say(f"  pre-July all-bar accuracy : "
    f"{np.mean((pre_pred[ok]>.5).astype(int)==pre_act)*100:.2f}%")
say(f"  pre-July top-5% accuracy  : "
    f"{np.mean((pre_pred[ok][m]>.5).astype(int)==pre_act[m])*100:.2f}%  "
    f"(n={m.sum()})")
say(f"  FROZEN THRESHOLD |p-0.5| >= {THR:.4f}")

# ---- STEP 2: walk July forward
say()
say("="*74)
say("STEP 2: WALK JULY 2026 FORWARD, ONE BAR AT A TIME")
say("="*74)
rows = []
for k in np.where(is_july)[0]:
    p = fit_predict(X[:k], lab[:k], X[k])       # train on everything before k
    c = abs(p-0.5)
    rows.append(dict(i=int(keep[k]), t=ts[keep[k]], p=p, conf=c,
                     call=1 if p > .5 else 0, actual=int(lab[k]),
                     med=med[k]))
say(f"  July predictions made: {len(rows)}")

allc = np.array([r['call'] == r['actual'] for r in rows])
say(f"\n  ALL July bars      : n={len(rows):4d}  "
    f"accuracy {allc.mean()*100:.2f}%")

fired = [r for r in rows if r['conf'] >= THR]
if fired:
    f = np.array([r['call'] == r['actual'] for r in fired])
    say(f"  FIRED (conf>=thr)  : n={len(fired):4d}  "
        f"accuracy {f.mean()*100:.2f}%   <-- THE CLAIM WAS 86.84%")
else:
    say("  no bars exceeded the frozen threshold in July")

# confidence ladder within July, using pre-July quantiles
say()
say("="*74)
say("STEP 3: FULL CONFIDENCE LADDER (thresholds all frozen pre-July)")
say("="*74)
say(f"{'bucket':22s} {'thr':>8s} {'n':>5s} {'accuracy':>10s}")
for q, name in [(0.0,'all July bars'), (.5,'top 50%'), (.8,'top 20%'),
                (.9,'top 10%'), (.95,'top 5%'), (.98,'top 2%')]:
    thr = float(np.quantile(pre_conf, q))
    sel = [r for r in rows if r['conf'] >= thr]
    if len(sel) < 3:
        say(f"{name:22s} {thr:8.4f} {len(sel):5d} {'n/a':>10s}"); continue
    a = np.mean([r['call'] == r['actual'] for r in sel])*100
    say(f"{name:22s} {thr:8.4f} {len(sel):5d} {a:9.2f}%")

# ---- STEP 3: every fired signal, listed
if fired:
    say()
    say("="*74)
    say("STEP 4: EVERY FIRED SIGNAL IN JULY 2026")
    say("="*74)
    say(f"{'time (UTC)':18s} {'score':>7s} {'call':>6s} {'actual':>7s} "
        f"{'next rng%':>10s} {'med%':>8s} {'hit':>5s}")
    for r in fired:
        nx = bars[r['i']+1]
        nr = (nx[1]-nx[2])/nx[0]
        say(f"{dt.datetime.utcfromtimestamp(r['t']):%Y-%m-%d %H:%M}  "
            f"{r['p']:7.3f} {'ABOVE' if r['call'] else 'BELOW':>6s} "
            f"{'ABOVE' if r['actual'] else 'BELOW':>7s} "
            f"{nr*100:9.4f} {r['med']*100:7.4f} "
            f"{'YES' if r['call']==r['actual'] else 'no':>5s}")

# ---- week by week
say()
say("="*74)
say("STEP 5: WEEK BY WEEK WITHIN JULY")
say("="*74)
byw = collections.defaultdict(list)
for r in rows:
    if r['conf'] >= THR:
        byw[dt.datetime.utcfromtimestamp(r['t']).isocalendar()[1]].append(
            r['call'] == r['actual'])
for w in sorted(byw):
    v = byw[w]
    say(f"  ISO week {w}  n={len(v):3d}  accuracy {np.mean(v)*100:6.2f}%")

say()
say("="*74)
say("VERDICT")
say("="*74)
if fired:
    a = np.mean([r['call'] == r['actual'] for r in fired])*100
    n = len(fired)
    se = np.sqrt(0.8684*(1-0.8684)/n)*100
    say(f"  claimed accuracy at top-5% : 86.84%")
    say(f"  July 2026 realised         : {a:.2f}%  (n={n})")
    say(f"  1 s.e. around the claim on n={n} is +/- {se:.1f} points")
    say(f"  -> {'CONFIRMED' if a >= 86.84-2*se else 'BELOW CLAIM'} "
        f"within 2 standard errors")
