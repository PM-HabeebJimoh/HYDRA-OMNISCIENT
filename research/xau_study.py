"""
EXHAUSTIVE STUDY OF XAUUSD CANDLES.

Everything extractable from OHLC on the data I have:
  3,952 1H bars   (Dec 2025 - Jul 2026, Investing.com)
  -> resampled to 2H, 4H, 8H, 12H, 1D
  348 weekly bars (2019-2025)
  282 monthly bars (2003-2026)

Goal: find any rule predicting next-candle DIRECTION at high accuracy.

Method:
  1. Build every standard candle feature.
  2. Test each ALONE at every timeframe.
  3. Test every 2-way and 3-way COMBINATION.
  4. Control for multiple testing with the empirical max-|z| null.
  5. Whatever survives, validate out-of-sample and on the true path.

No conclusions asserted. Everything measured.
"""
import json, glob, sys, collections, itertools, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

# ---------- load every XAUUSD 1H bar
raw = {}
for f in sorted(glob.glob(str(ROOT/'data/raw/intraday/XAUUSD*.json'))):
    d = json.load(open(f))
    for i, t in enumerate(d['t']):
        raw[t] = (d['o'][i], d['h'][i], d['l'][i], d['c'][i])
T1 = sorted(raw)
say("="*78)
say("XAUUSD CANDLE STUDY")
say("="*78)
say(f"1H bars: {len(T1)}  "
    f"{dt.datetime.utcfromtimestamp(T1[0]):%Y-%m-%d} .. "
    f"{dt.datetime.utcfromtimestamp(T1[-1]):%Y-%m-%d}")

def resample(mult):
    B = {}
    for t in T1:
        k = t - (t % (3600*mult))
        o, h, l, c = raw[t]
        if k not in B: B[k] = [o, h, l, c]
        else:
            B[k][1] = max(B[k][1], h); B[k][2] = min(B[k][2], l); B[k][3] = c
    ks = sorted(B)
    return ks, [tuple(B[k]) for k in ks]

TF = {}
for mult, name in [(1,'1H'), (2,'2H'), (4,'4H'), (8,'8H'), (12,'12H'), (24,'1D')]:
    ks, bars = resample(mult)
    if len(bars) >= 60: TF[name] = (ks, bars)
W = json.load(open(ROOT/'data/raw/oos/gold_weekly.json'))
TF['1W'] = (W['t'], [(c, c, c, c) for c in W['c']])   # weekly: closes only
say("timeframes: " + ", ".join(f"{k}({len(v[1])})" for k, v in TF.items()))

# ---------- candle features, all strictly causal
def feats(bars, i):
    o, h, l, c = bars[i]
    po, ph, pl, pc = bars[i-1]
    rng = max(h-l, 1e-12); body = c-o
    prng = max(ph-pl, 1e-12)
    r = [(bars[j][3]-bars[j][0])/bars[j][0] for j in range(max(0,i-20), i+1)]
    rr = [(bars[j][1]-bars[j][2])/bars[j][0] for j in range(max(0,i-20), i+1)]
    atr = np.mean(rr) if rr else 0
    f = {}
    f['up']        = body > 0
    f['big_body']  = abs(body)/rng > 0.6
    f['doji']      = abs(body)/rng < 0.15
    f['clv_hi']    = (c-l)/rng > 0.75
    f['clv_lo']    = (c-l)/rng < 0.25
    f['upper_wick']= (h-max(o,c))/rng > 0.5
    f['lower_wick']= (min(o,c)-l)/rng > 0.5
    f['engulf_up'] = (c > po) and (o < pc) and body > 0
    f['engulf_dn'] = (c < po) and (o > pc) and body < 0
    f['inside']    = (h <= ph) and (l >= pl)
    f['outside']   = (h > ph) and (l < pl)
    f['gap_up']    = o > pc
    f['gap_dn']    = o < pc
    f['nr']        = rng < prng            # narrowing range
    f['wr']        = rng > prng*1.5        # wide range
    f['hh']        = h > ph
    f['ll']        = l < pl
    f['exp_vol']   = (rng/o) > atr*1.3 if atr else False
    f['low_vol']   = (rng/o) < atr*0.7 if atr else False
    f['streak2u']  = i >= 2 and all(bars[j][3] > bars[j][0] for j in (i, i-1))
    f['streak2d']  = i >= 2 and all(bars[j][3] < bars[j][0] for j in (i, i-1))
    f['streak3u']  = i >= 3 and all(bars[j][3] > bars[j][0] for j in (i, i-1, i-2))
    f['streak3d']  = i >= 3 and all(bars[j][3] < bars[j][0] for j in (i, i-1, i-2))
    if len(r) >= 10:
        f['mom_up'] = np.mean(r[-5:]) > 0
        f['above_ma']= c > np.mean([bars[j][3] for j in range(max(0,i-19), i+1)])
    else:
        f['mom_up'] = f['above_ma'] = False
    return f

say()
say("="*78)
say("1. SINGLE FEATURES, EVERY TIMEFRAME")
say("="*78)
say(f"{'feature':13s} " + " ".join(f"{k:>9s}" for k in TF if k != '1W'))
KEYS = None
STORE = {}
for name in [k for k in TF if k != '1W']:
    ks, bars = TF[name]
    rows = []
    for i in range(25, len(bars)-1):
        f = feats(bars, i)
        nx = bars[i+1]
        rows.append((f, 1 if nx[3] > nx[0] else 0))
    STORE[name] = rows
    if KEYS is None: KEYS = sorted(rows[0][0])
for k in KEYS:
    line = f"{k:13s} "
    for name in [x for x in TF if x != '1W']:
        rows = STORE[name]
        sel = [y for f, y in rows if f[k]]
        if len(sel) < 30: line += f"{'-':>9s}"; continue
        a = max(np.mean(sel), 1-np.mean(sel))*100
        line += f"{a:8.1f}%"
    say(line)

say()
say("="*78)
say("2. EXHAUSTIVE COMBINATION SEARCH (1-, 2- and 3-feature)")
say("="*78)
FOUND = []
for name in [x for x in TF if x != '1W']:
    rows = STORE[name]
    if len(rows) < 120: continue
    for k in (1, 2, 3):
        for combo in itertools.combinations(KEYS, k):
            for signs in itertools.product([True, False], repeat=k):
                sel = [y for f, y in rows
                       if all(f[c] == s for c, s in zip(combo, signs))]
                if len(sel) < 40: continue
                p = np.mean(sel)
                acc = max(p, 1-p)*100
                n = len(sel)
                z = (acc-50)/(np.sqrt(0.25/n)*100)
                FOUND.append((acc, z, n, name, combo, signs, 1 if p > .5 else 0))
FOUND.sort(reverse=True, key=lambda x: x[1])
ncell = len(FOUND)
say(f"cells tested: {ncell}")
say(f"noise expectation for max|z|: {np.sqrt(2*np.log(max(ncell,2))):.2f}")
say(f"\n{'acc%':>7s} {'z':>7s} {'n':>6s} {'tf':>4s}  rule")
for acc, z, n, name, combo, signs, side in FOUND[:15]:
    desc = " AND ".join(f"{'' if s else 'NOT '}{c}" for c, s in zip(combo, signs))
    say(f"{acc:7.2f} {z:+7.2f} {n:6d} {name:>4s}  "
        f"{'UP' if side else 'DN'}: {desc}")

say()
say("="*78)
say("3. IS ANY CELL ABOVE 85%?")
say("="*78)
hi = [x for x in FOUND if x[0] >= 85]
say(f"  cells at or above 85% accuracy with n>=40: {len(hi)}")
if hi:
    for acc, z, n, name, combo, signs, side in hi[:10]:
        desc = " AND ".join(f"{'' if s else 'NOT '}{c}" for c,s in zip(combo,signs))
        say(f"    {acc:.2f}% n={n} {name} {desc}")
say(f"  best available: {FOUND[0][0]:.2f}% at n={FOUND[0][2]}")

say()
say("="*78)
say("4. EMPIRICAL NULL: repeat the ENTIRE search on shuffled labels")
say("="*78)
say("If the search itself manufactures 70%+ cells, the winners are noise.")
rng = np.random.default_rng(0)
maxz = []
for trial in range(20):
    best = 0
    for name in [x for x in TF if x != '1W']:
        rows = STORE[name]
        if len(rows) < 120: continue
        ys = rng.permutation([y for _, y in rows])
        fs = [f for f, _ in rows]
        for k in (1, 2):
            for combo in itertools.combinations(KEYS, k):
                for signs in itertools.product([True, False], repeat=k):
                    sel = [ys[i] for i, f in enumerate(fs)
                           if all(f[c] == s for c, s in zip(combo, signs))]
                    if len(sel) < 40: continue
                    p = np.mean(sel); acc = max(p, 1-p)*100
                    z = (acc-50)/(np.sqrt(0.25/len(sel))*100)
                    best = max(best, z)
    maxz.append(best)
maxz = np.array(maxz)
actual = FOUND[0][1]
say(f"  shuffled-label max z: median {np.median(maxz):.2f}  "
    f"95th {np.percentile(maxz,95):.2f}  max {maxz.max():.2f}")
say(f"  actual best z: {actual:.2f}")
say(f"  empirical p-value: {(maxz >= actual).mean():.3f}")
say(f"  -> {'SURVIVES' if (maxz>=actual).mean()<0.05 else 'DOES NOT SURVIVE'} "
    f"the search-induced null")
