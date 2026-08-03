"""
AUDIT the horizon result.

Raw finding: "real yield BELOW its 52w median -> gold falls over 26w"
             acc 34.44% (i.e. 65.56% the other way), t=-7.13, p=0.0000

Two things must be settled before this is anything:

  1. THE TREND CONTROL. Gold went $1,287 -> $3,587 in this window. Long-only
     at h=26w has t=+14.61 and a 77.95% up-rate. A signal that is long only
     SOME of the time will look "wrong" simply by being out of a rising market.
     The inverted result may be nothing but "you were flat/short during the
     biggest bull run in gold's history."
     -> Test EXCESS return over always-long, and test the long and short legs
        separately.

  2. OVERLAPPING WINDOWS. 26-week forward returns sampled weekly overlap 25/26.
     The effective sample is ~270/26 = 10 independent observations, not 270.
     The naive t is inflated by ~sqrt(26) = 5.1x.
     -> t=-7.13 / 5.1 = -1.4. That alone may erase it.

Both are standard, both are fatal if they bite. Testing.
"""
import json, sys, csv, datetime as dt, collections, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'research'))
from calendar_edge import tstat, signflip_null

def say(*a): print(*a, flush=True)

W = json.load(open(ROOT / 'data/raw/oos/gold_weekly.json'))
gold = {dt.date.fromtimestamp(t): c for t, c in zip(W['t'], W['c'])}
gd = sorted(gold)
RY = json.load(open(ROOT / 'data/raw/weekly/DFII10_W.json'))
ry = {dt.date.fromisoformat(x): v for x, v in zip(RY['dates'], RY['v'])}

def latest(m, d, maxlag=14):
    best, bd = None, None
    for k in sorted(m):
        if k < d: best, bd = m[k], k
        else: break
    return None if (bd is None or (d-bd).days > maxlag) else best

P = []
for i, d in enumerate(gd):
    r = latest(ry, d)
    if r is not None:
        P.append(dict(i=i, d=d, ry=r))

def fwd(i, h):
    return None if i+h >= len(gd) else (gold[gd[i+h]]-gold[gd[i]])/gold[gd[i]]

def build(h):
    """signal, forward return, date -- expanding median, no look-ahead."""
    out, hist = [], []
    for p in P:
        if len(hist) >= 52:
            s = 1 if p['ry'] < float(np.median(hist)) else -1
            f = fwd(p['i'], h)
            if f is not None:
                out.append((p['d'], s, f))
        hist.append(p['ry'])
    return out

say("="*78)
say("1. THE TREND CONTROL -- is it a signal, or just being out of a bull run?")
say("="*78)
say(f"{'h':>3s} {'sig mean%':>10s} {'long-only%':>11s} {'EXCESS%':>9s} "
    f"{'t(excess)':>10s} {'long leg':>10s} {'short leg':>10s}")
for h in (1, 2, 4, 8, 13, 26):
    rows = build(h)
    sig = np.array([s*f for _, s, f in rows])
    raw = np.array([f for _, _, f in rows])
    exc = sig - raw                     # excess over always-long
    m1, t1, _ = tstat(list(sig))
    m2, _, _ = tstat(list(raw))
    me, te, _ = tstat(list(exc))
    lo = [f for _, s, f in rows if s > 0]
    sh = [f for _, s, f in rows if s < 0]
    ml, tl, nl = tstat(lo)
    ms, ts_, ns = tstat(sh)
    say(f"{h:3d} {m1*100:+10.3f} {m2*100:+11.3f} {me*100:+9.3f} {te:+10.2f} "
        f"{ml*100:+7.2f}(n{nl:3d}) {ms*100:+7.2f}(n{ns:3d})")
say("""
Read the last two columns. If the 'short leg' (high real yield) is simply
LESS positive than the long leg rather than negative, the signal is not
predicting direction -- it is predicting how much of a rising market you
captured. That is beta timing, not direction.""")

say()
say("="*78)
say("2. OVERLAPPING WINDOWS -- the naive t is inflated by ~sqrt(h)")
say("="*78)
say(f"{'h':>3s} {'naive t':>9s} {'sqrt(h)':>8s} {'adj t':>7s} "
    f"{'non-overlap n':>14s} {'non-overlap t':>14s}")
for h in (1, 2, 4, 8, 13, 26):
    rows = build(h)
    sig = [s*f for _, s, f in rows]
    m, t, n = tstat(sig)
    # strictly non-overlapping: take every h-th observation
    nov = sig[::h]
    mn, tn, nn = tstat(nov)
    say(f"{h:3d} {t:+9.2f} {np.sqrt(h):8.2f} {t/np.sqrt(h):+7.2f} "
        f"{nn:14d} {tn:+14.2f}")
say("""
The 'non-overlap' column is the honest one: it samples each forward window
once, so observations are independent.""")

say()
say("="*78)
say("3. NON-OVERLAPPING *EXCESS* RETURN -- both corrections at once")
say("="*78)
say(f"{'h':>3s} {'n':>5s} {'excess%':>9s} {'t':>7s} {'p(flip)':>9s} {'acc%':>7s}")
for h in (1, 2, 4, 8, 13, 26):
    rows = build(h)
    exc = [s*f - f for _, s, f in rows][::h]
    acc = [int(np.sign(f) == s) for _, s, f in rows][::h]
    if len(exc) < 8:
        say(f"{h:3d} {len(exc):5d}   too few independent observations")
        continue
    m, t, n = tstat(exc)
    p = signflip_null(exc)
    say(f"{h:3d} {n:5d} {m*100:+9.3f} {t:+7.2f} {p:9.4f} {np.mean(acc)*100:7.2f}")

say()
say("="*78)
say("4. SUB-PERIOD STABILITY (does it hold in both halves of 7.6 years?)")
say("="*78)
for h in (4, 13, 26):
    rows = build(h)
    half = rows[len(rows)//2][0]
    for lab, sel in [('2019-2022', [r for r in rows if r[0] < half]),
                     ('2022-2025', [r for r in rows if r[0] >= half])]:
        exc = [s*f - f for _, s, f in sel][::h]
        if len(exc) < 5: continue
        m, t, n = tstat(exc)
        say(f"  h={h:2d}w {lab}  n={n:3d}  excess {m*100:+7.3f}%  t={t:+5.2f}")

say()
say("="*78)
say("VERDICT")
say("="*78)
rows = build(26)
exc = [s*f - f for _, s, f in rows][::26]
m, t, n = tstat(exc)
say(f"  Headline was t=-7.13 on 270 overlapping 26-week windows.")
say(f"  Honest: {n} independent windows, excess return {m*100:+.3f}%, t={t:+.2f}")
if abs(t) < 1.96:
    say("  -> The signal does NOT survive. It was overlap inflation plus")
    say("     the gold bull market, not directional information.")
else:
    say("  -> Survives both corrections. This is real and needs pursuing.")
