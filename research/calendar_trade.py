"""
Does the calendar's ADVANCE volatility knowledge convert into money?

The verified 4H bracket (prior session: n=1978, t=+2.76, sign-flip p=0.0020)
is a MAGNITUDE bet: straddle-like, pays when the bar moves, loses on whipsaw.
The prior anticipatory attempt failed because it forecast range from the CHART
-- and the bracket width, being an ATR multiple, rose with the forecast, so
signal and threshold cancelled.

The calendar is different in exactly the way that matters:
  * it is known days in advance, so it cannot be in today's ATR
  * it predicts range EXOGENOUSLY, so the bracket width does NOT move with it

So: hold the bracket width fixed at the ATR the chart implies, and let the
calendar tell you WHEN the true range will exceed it. That is the one
configuration in which an anticipatory range forecast is monetisable.

Worst-case whipsaw accounting throughout (both triggers in one bar = full
double loss), real spreads, no basket cap, no survivorship deletion.
"""
import sys, datetime as dt, collections
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events, tstat, signflip_null

# real half-spreads, fraction of price (as used in the prior verified test)
SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}

p1h = load_1h()
b1 = sorted(p1h)
p4 = resample_4h(p1h)
b4 = sorted(p4)

events = build_events()
ev_ts = [e['ts'] for e in events]

# ---- calendar feature per 4H bar: how many releases are SCHEDULED in it.
# Known days in advance. Uses only the schedule, never the numbers.
sched4 = collections.Counter()
for ts in ev_ts:
    sched4[ts - (ts % 14400)] += 1

def atr(series, i, n=20):
    """True range average over the n bars BEFORE i. Strictly causal."""
    tr = []
    for j in range(max(0, i - n), i):
        bar = series[j]
        tr.append(max(bar['h'] - bar['l'],
                      abs(bar['h'] - bar['pc']),
                      abs(bar['l'] - bar['pc'])) / bar['pc'])
    return np.mean(tr) if tr else None

def bracket(o, h, l, c, width, halfspread):
    """Straddle bracket around the open. Worst case: if BOTH sides trigger in
    the same bar we book the full double loss (we cannot know which came
    first from OHLC, so we assume the worst)."""
    up, dn = o * (1 + width), o * (1 - width)
    hit_u, hit_d = h >= up, l <= dn
    if hit_u and hit_d:
        return -2 * width - 2 * halfspread          # whipsawed both ways
    if hit_u:
        return (c - up) / o - halfspread            # long from up-break
    if hit_d:
        return (dn - c) / o - halfspread            # short from down-break
    return 0.0                                      # never triggered, no trade

def run(assets=A, wmult=1.0, cal_filter=None, label=''):
    rows = []
    for a in assets:
        ser = []
        prevc = None
        for t in b4:
            d = p4[t][a]
            ser.append(dict(t=t, o=d['open'], h=d['high'], l=d['low'],
                            c=d['close'], pc=prevc if prevc else d['open']))
            prevc = d['close']
        for i in range(21, len(ser)):
            A_ = atr(ser, i)
            if not A_: continue
            bar = ser[i]
            nrel = sched4.get(bar['t'], 0)
            if cal_filter is not None and not cal_filter(nrel):
                continue
            r = bracket(bar['o'], bar['h'], bar['l'], bar['c'],
                        wmult * A_, SPREAD[a])
            if r == 0: continue
            rows.append((bar['t'], a, r, nrel))
    pnl = [r[2] for r in rows]
    m, t, n = tstat(pnl)
    wr = np.mean([v > 0 for v in pnl]) * 100 if pnl else np.nan
    return dict(label=label, m=m, t=t, n=n, wr=wr, rows=rows, pnl=pnl)

print("=" * 78)
print("4H BRACKET, SPLIT BY WHAT THE CALENDAR SAID DAYS AGO")
print("=" * 78)
print(f"{'bucket':34s} {'n':>5s} {'mean%':>9s} {'t':>7s} {'WR%':>7s}")
res = {}
for lbl, f in [('ALL bars (baseline)',        None),
               ('NO release scheduled',       lambda k: k == 0),
               ('>=1 release scheduled',      lambda k: k >= 1),
               ('>=2 releases scheduled',     lambda k: k >= 2),
               ('>=3 releases scheduled',     lambda k: k >= 3)]:
    r = run(cal_filter=f, label=lbl)
    res[lbl] = r
    print(f"{lbl:34s} {r['n']:5d} {r['m']*100:+9.4f} {r['t']:+7.2f} {r['wr']:7.1f}")

print()
print("=" * 78)
print("MONOTONICITY: mean bracket PnL by exact number of scheduled releases")
print("=" * 78)
allr = run(label='all')['rows']
byk = collections.defaultdict(list)
for _, _, r, k in allr:
    byk[min(k, 3)].append(r)
for k in sorted(byk):
    m, t, n = tstat(byk[k])
    lab = f"{k}+" if k == 3 else str(k)
    print(f"  {lab} releases scheduled   n={n:5d}   mean {m*100:+.4f}%   t={t:+5.2f}")

print()
print("=" * 78)
print("VALIDATION OF THE TRADED BUCKET (>=1 release scheduled)")
print("=" * 78)
r = res['>=1 release scheduled']
pnl = np.asarray(r['pnl'])
print(f"  n={r['n']}  mean {r['m']*100:+.4f}%  t={r['t']:+.2f}  WR {r['wr']:.1f}%")
p = signflip_null(list(pnl))
print(f"  sign-flip null                p = {p:.4f}")
half = len(pnl) // 2
for lbl, s in [('first half ', pnl[:half]), ('second half', pnl[half:])]:
    m, t, n = tstat(list(s))
    print(f"  {lbl}  n={n:5d}  mean {m*100:+.4f}%  t={t:+5.2f}")

# month by month, out of sample in time
print()
print("  month by month (traded bucket):")
bym = collections.defaultdict(list)
for t_, a, x, k in r['rows']:
    bym[dt.datetime.utcfromtimestamp(t_).strftime('%Y-%m')].append(x)
pos = 0
for k in sorted(bym):
    m, tt, n = tstat(bym[k])
    pos += m > 0
    print(f"    {k}  n={n:4d}  mean {m*100:+.4f}%  t={tt:+5.2f}")
print(f"    -> {pos} of {len(bym)} months positive")

print()
print("=" * 78)
print("THE INCREMENT: does the calendar ADD to the chart, or just restate it?")
print("=" * 78)
print("""
Regress bracket PnL on (a) the chart's own range forecast -- today's ATR
relative to its own trailing level -- and (b) the calendar count. If the
calendar coefficient survives controlling for the chart, it is new
information: the thing that happens BEFORE the chart reacts.
""")
X, y = [], []
for a in A:
    ser = []; prevc = None
    for t in b4:
        d = p4[t][a]
        ser.append(dict(t=t, o=d['open'], h=d['high'], l=d['low'],
                        c=d['close'], pc=prevc if prevc else d['open']))
        prevc = d['close']
    for i in range(61, len(ser)):
        a20 = atr(ser, i, 20); a60 = atr(ser, i, 60)
        if not a20 or not a60: continue
        bar = ser[i]
        r_ = bracket(bar['o'], bar['h'], bar['l'], bar['c'], a20, SPREAD[a])
        if r_ == 0: continue
        X.append([1.0, a20 / a60 - 1.0, float(sched4.get(bar['t'], 0))])
        y.append(r_)
X = np.asarray(X); y = np.asarray(y)
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
resid = y - X @ beta
s2 = resid @ resid / (len(y) - X.shape[1])
se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
for nm, b_, s_ in zip(['intercept', 'chart ATR20/ATR60-1', 'CALENDAR count'],
                      beta, se):
    print(f"  {nm:24s} coef {b_*100:+8.4f}%   t = {b_/s_:+6.2f}")
print(f"  n = {len(y)}")
