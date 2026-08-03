"""
AUDIT THE JULY 15/15.

Two things in the July output are suspicious and must be checked:

  1. ALL 15 fired signals were "ABOVE" calls. The model never fires BELOW.
     Ridge output is unbounded (scores up to 1.418), so |p-0.5| is far
     easier to exceed on the upside. The "top 5% confidence" bucket may
     simply BE the "predict ABOVE" bucket.

  2. ALL 15 clustered at 12:00-14:00 and 18:00-19:00 UTC -- the US
     session and news window. Hour-of-day is one of the 14 features.
     If a trivial hour-only rule matches this, the model adds nothing.

Both are tested here against the honest benchmark.
"""
import json, glob, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'scripts')); sys.path.insert(0, str(ROOT/'research'))
from xau_range_predictor import (load_bars, features, trailing_median_range,
                                 fit_predict, LOOKBACK, MIN_TRAIN)
def say(*a): print(*a, flush=True)

ts, bars = load_bars()
X, lab, med, keep = [], [], [], []
for i in range(LOOKBACK+4, len(bars)-1):
    X.append(features(bars, i, ts))
    m = trailing_median_range(bars, i)
    nx = bars[i+1]
    med.append(m); lab.append(1 if (nx[1]-nx[2])/nx[0] > m else 0); keep.append(i)
X = np.array(X); lab = np.array(lab, float); keep = np.array(keep)
mon = np.array([dt.datetime.utcfromtimestamp(ts[i]).strftime('%Y-%m') for i in keep])
hr  = np.array([dt.datetime.utcfromtimestamp(ts[i]).hour for i in keep])
is_july = mon == '2026-07'
pre = ~is_july & (keep < keep[is_july][0])

say("="*74)
say("1. IS THE 'TOP 5% CONFIDENCE' BUCKET JUST 'PREDICT ABOVE'?")
say("="*74)
pre_idx = np.where(pre)[0]
pp = np.array([fit_predict(X[:k], lab[:k], X[k]) if k >= MIN_TRAIN else np.nan
               for k in pre_idx])
ok = ~np.isnan(pp)
conf = np.abs(pp[ok]-0.5); THR = float(np.quantile(conf, .95))
sel = conf >= THR
above = (pp[ok][sel] > .5)
say(f"  pre-July fired signals: {sel.sum()}")
say(f"    predicted ABOVE: {above.sum()}   predicted BELOW: {(~above).sum()}")
say(f"  ridge score range: {pp[ok].min():.3f} .. {pp[ok].max():.3f}")
say("  -> ridge is unbounded; |p-0.5| is asymmetric by construction.")
say("     The high-confidence bucket is effectively 'strong ABOVE' only.")

say()
say("="*74)
say("2. THE HONEST BENCHMARK: what does HOUR ALONE achieve?")
say("="*74)
say("  For each UTC hour, unconditional P(next range > trailing median),")
say("  computed on PRE-JULY data only, then applied to July.")
base = {}
for h in range(24):
    m = pre & (hr == h)
    if m.sum() >= 20: base[h] = lab[m].mean()
say(f"  {'hour':>5s} {'pre-July P(ABOVE)':>19s} {'n':>6s}")
for h in sorted(base, key=lambda x: -base[x])[:8]:
    say(f"  {h:5d} {base[h]*100:18.1f}% {(pre&(hr==h)).sum():6d}")

# hour-only rule on July: predict ABOVE when that hour's prior rate > 0.5
jl = np.where(is_july)[0]
hour_hits, model_hits, both = [], [], []
pj = []
for k in jl:
    p = fit_predict(X[:k], lab[:k], X[k]); pj.append(p)
pj = np.array(pj)
cj = np.abs(pj-0.5)
fired = cj >= THR
say()
say("  JULY comparison on the SAME 15 bars the model fired on:")
idx_f = jl[fired]
hr_f = hr[idx_f]; act_f = lab[idx_f].astype(int)
hour_call = np.array([1 if base.get(h, .5) > .5 else 0 for h in hr_f])
say(f"    model accuracy      : {np.mean((pj[fired]>.5).astype(int)==act_f)*100:.1f}%")
say(f"    hour-only accuracy  : {np.mean(hour_call==act_f)*100:.1f}%")
say(f"    always-say-ABOVE    : {np.mean(act_f==1)*100:.1f}%")
say(f"    hours that fired    : {sorted(collections.Counter(hr_f).items())}")

say()
say("="*74)
say("3. THE DECISIVE TEST: base rate at those hours vs model accuracy")
say("="*74)
say("  If a bar at 13:00 UTC has an 80% prior chance of exceeding its")
say("  trailing median, then 15/15 is far less impressive than it looks.")
for h in sorted(set(hr_f)):
    m = pre & (hr == h)
    say(f"    {h:02d}:00 UTC  pre-July P(ABOVE) = {lab[m].mean()*100:5.1f}%  "
        f"(n={m.sum()})  fired {list(hr_f).count(h)}x in July")
prior = np.mean([lab[pre & (hr == h)].mean() for h in hr_f])
say(f"\n  average prior for the fired hours: {prior*100:.1f}%")
say(f"  probability of 15/15 by that prior alone: {prior**15*100:.2f}%")

say()
say("="*74)
say("4. WHAT THE MODEL ACTUALLY ADDS -- matched-hour comparison")
say("="*74)
say("  Compare fired bars against ALL July bars at the SAME hours.")
same_hr = np.array([h in set(hr_f) for h in hr[jl]])
say(f"    all July bars at fired hours : n={same_hr.sum():3d}  "
    f"P(ABOVE) {lab[jl][same_hr].mean()*100:.1f}%")
say(f"    model-selected subset        : n={fired.sum():3d}  "
    f"P(ABOVE) {act_f.mean()*100:.1f}%")
lift = act_f.mean()*100 - lab[jl][same_hr].mean()*100
say(f"    LIFT FROM THE MODEL          : {lift:+.1f} percentage points")

say()
say("="*74)
say("VERDICT")
say("="*74)
say(f"""  July result 15/15 = 100% is REAL but must be read correctly:

  * the fired bars sit at hours whose unconditional ABOVE-rate is
    already {prior*100:.0f}%
  * matched against other July bars at the same hours, the model's
    lift is {lift:+.1f} points
  * n=15 is far too small to distinguish 100% from 87%
  * the model only ever fires ABOVE, so it is a
    "volatility expansion detector", not a two-sided classifier""")
