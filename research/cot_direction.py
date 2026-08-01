"""
POSITIONING: the last pre-chart category, and the one that historically
carries DIRECTION rather than only size.

Data: CFTC Commitments of Traders, legacy futures-only, 48 weeks x 3 markets
(GOLD/COMEX, EURO FX/CME, AUSTRALIAN DOLLAR/CME), Sep 2025 - Jul 2026.
Real, free, official. data/raw/cot/cot_3assets.json

THE TIMING TRAP, HANDLED UP FRONT:
COT positions are AS OF Tuesday close but PUBLISHED Friday 15:30 ET.
Using the Tuesday date is a 3-day look-ahead and is how most COT "edges"
are manufactured. Everything below is lagged to the FRIDAY RELEASE and
traded from the FOLLOWING MONDAY open. Both are reported so the difference
is visible.

Angles tested (positioning is a level, so several distinct logics apply):
  1. TREND     - follow big specs
  2. CONTRARIAN- fade crowded specs (the classic claim)
  3. EXTREME   - only act at percentile extremes of the spec net
  4. FLOW      - week-over-week CHANGE in spec net, not the level
  5. COMMERCIAL- follow the hedgers instead (the "smart money" claim)
  6. OI CONFIRM- spec net scaled by open interest
"""
import json, sys, glob, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, A
from calendar_edge import tstat, signflip_null

COT = json.load(open(ROOT / 'data/raw/cot/cot_3assets.json'))

# ---- daily prices from the 1H feed (real Investing.com bars)
p1h = load_1h()
daily = collections.defaultdict(dict)
for ts in sorted(p1h):
    d = dt.datetime.utcfromtimestamp(ts).date()
    for a in A:
        b = p1h[ts][a]
        if a not in daily[d]:
            daily[d][a] = dict(o=b['open'], c=b['close'])
        else:
            daily[d][a]['c'] = b['close']
days = sorted(d for d in daily if len(daily[d]) == 3)
print(f"daily bars (3-asset complete): {len(days)}  {days[0]} .. {days[-1]}")

def next_trading_day(d):
    for x in days:
        if x > d:
            return x
    return None

def fwd_ret(d0, a, nd=5):
    """Open of the first day after d0, held nd trading days to close."""
    i = None
    for k, x in enumerate(days):
        if x > d0:
            i = k; break
    if i is None or i + nd - 1 >= len(days):
        return None
    o = daily[days[i]][a]['o']
    c = daily[days[i + nd - 1]][a]['c']
    return (c - o) / o

# ---- build weekly positioning features
def features(asset):
    rows = COT[asset]
    out = []
    net_hist = []
    for k, (ds, nl, ns, cl, cs, oi) in enumerate(rows):
        asof = dt.date.fromisoformat(ds)
        # PUBLICATION date: Friday of the same week (as-of is Tuesday)
        pub = asof + dt.timedelta(days=3)
        net = nl - ns                      # non-commercial (spec) net
        cnet = cl - cs                     # commercial net
        r = dict(asof=asof, pub=pub, net=net, cnet=cnet, oi=oi,
                 net_oi=net / oi, cnet_oi=cnet / oi)
        # week-over-week flow
        r['dnet'] = net - rows[k-1][1] + rows[k-1][2] if k > 0 else None
        # percentile of net within PRIOR history only (no look-ahead)
        r['pct'] = (float(np.mean([h < net for h in net_hist]))
                    if len(net_hist) >= 12 else None)
        net_hist.append(net)
        out.append(r)
    return out

FEAT = {a: features(a) for a in A}

def run(signal_fn, use_pub=True, nd=5, label=''):
    """signal_fn(row)-> +1/-1/0 ; trades from the day AFTER pub (or asof)."""
    pnl = []
    for a in A:
        for r in FEAT[a]:
            s = signal_fn(r)
            if not s:
                continue
            anchor = r['pub'] if use_pub else r['asof']
            x = fwd_ret(anchor, a, nd)
            if x is None:
                continue
            pnl.append(s * x)
    m, t, n = tstat(pnl)
    return dict(label=label, m=m, t=t, n=n, pnl=pnl,
                wr=(np.mean([v > 0 for v in pnl]) * 100 if pnl else np.nan))

ANGLES = [
    ('1 TREND  spec net > 0',        lambda r: 1 if r['net'] > 0 else -1),
    ('2 CONTRA fade spec net',       lambda r: -1 if r['net'] > 0 else 1),
    ('3 EXTREME pct>0.8 fade',       lambda r: (-1 if r['pct'] > 0.8 else
                                                (1 if r['pct'] < 0.2 else 0))
                                     if r['pct'] is not None else 0),
    ('3b EXTREME pct>0.8 follow',    lambda r: (1 if r['pct'] > 0.8 else
                                                (-1 if r['pct'] < 0.2 else 0))
                                     if r['pct'] is not None else 0),
    ('4 FLOW  d(spec net) follow',   lambda r: (np.sign(r['dnet'])
                                                if r['dnet'] else 0)),
    ('4b FLOW d(spec net) fade',     lambda r: (-np.sign(r['dnet'])
                                                if r['dnet'] else 0)),
    ('5 COMMERCIAL follow',          lambda r: 1 if r['cnet'] > 0 else -1),
    ('6 net/OI > median follow',     lambda r: 1 if r['net_oi'] > 0 else -1),
]

for nd, hlab in [(5, 'hold 5 trading days (1 week)'),
                 (10, 'hold 10 trading days (2 weeks)')]:
    print()
    print("=" * 78)
    print(f"DIRECTION FROM POSITIONING -- {hlab}")
    print("   'asof' column = Tuesday date (LOOK-AHEAD, shown for contrast)")
    print("   'pub'   column = traded after Friday release (HONEST)")
    print("=" * 78)
    print(f"{'angle':32s} {'n':>4s} {'t(asof)':>9s} {'t(PUB)':>8s} "
          f"{'mean%':>8s} {'WR%':>6s}")
    results = []
    for lab, fn in ANGLES:
        ra = run(fn, use_pub=False, nd=nd, label=lab)
        rp = run(fn, use_pub=True, nd=nd, label=lab)
        results.append(rp)
        print(f"{lab:32s} {rp['n']:4d} {ra['t']:+9.2f} {rp['t']:+8.2f} "
              f"{rp['m']*100:+8.3f} {rp['wr']:6.1f}")
    ts = [abs(r['t']) for r in results]
    print(f"  -> |t| max {max(ts):.2f}, mean {np.mean(ts):.2f}; "
          f"{sum(1 for x in ts if x > 1.96)} of {len(ts)} exceed 1.96 "
          f"(chance expects {0.05*len(ts):.1f})")
    best = max(results, key=lambda r: abs(r['t']))
    print(f"  -> best: {best['label']}  t={best['t']:+.2f}  "
          f"sign-flip p={signflip_null(best['pnl']):.4f}")

# ------------------------------------------------------------------
print()
print("=" * 78)
print("PER-ASSET BREAKDOWN OF THE STRONGEST ANGLE (honest, pub-lagged)")
print("=" * 78)
for lab, fn in ANGLES:
    row = []
    for a in A:
        pnl = []
        for r in FEAT[a]:
            s = fn(r)
            if not s: continue
            x = fwd_ret(r['pub'], a, 5)
            if x is None: continue
            pnl.append(s * x)
        m, t, n = tstat(pnl)
        row.append(f"{a}: t={t:+5.2f}")
    print(f"  {lab:32s} " + "   ".join(row))
