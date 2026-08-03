"""
FX ONLY. FORCED FLOWS -- the one cause that is NOT a forecast.

Question: what makes someone BUY or SELL currency when they do not want to?
Answer: mandates. Forced flows happen on a schedule, for reasons outside
the market, by participants who are price-insensitive.

  1. MONTH-END REBALANCE. Global equity funds hold foreign stocks and hedge
     the FX. When equities rise, the hedge is too small; they must SELL the
     foreign currency at month end to re-hedge. Mechanical, dated, and the
     size is set by the equity move -- which is already known.
  2. TURN-OF-MONTH. Pension contributions, coupon payments, index rolls.
  3. LONDON 4PM FIX. Benchmark orders concentrated in one minute.
  4. QUARTER-END. Same as month-end but larger.

These are knowable BEFORE the move. Nobody has to predict anything.

Data: real Investing.com 1H FX (EURUSD, AUDUSD, GBPUSD, USDCAD)
      real FRED monthly EURUSD/USDJPY 23.6 years
"""
import json, sys, glob, collections, calendar, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'scripts')); sys.path.insert(0, str(ROOT/'research'))
from intraday_engine import load_1h, A
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

SPREAD = {'eur':0.000045,'aud':0.000075,'gbp':0.00006,'cad':0.00008}

# FX only -- drop gold
p1h = load_1h()
P = {a: {t: p1h[t][a] for t in p1h} for a in A if a != 'gold'}
for f in glob.glob(str(ROOT/'data/raw/intraday_x/*.json')):
    r = json.load(open(f))
    nm = {'GBPUSD':'gbp','USDCAD':'cad'}.get(r.get('symbol'))
    if nm:
        P[nm] = {ts: dict(open=r['o'][i],high=r['h'][i],low=r['l'][i],
                          close=r['c'][i]) for i,ts in enumerate(r['t'])}
FX = [a for a in P if len(P[a]) > 300]
say(f"FX instruments: {FX}")

# ---------- daily bars
DAY = {}
for a in FX:
    d = collections.defaultdict(list)
    for ts in sorted(P[a]):
        d[dt.datetime.utcfromtimestamp(ts).date()].append((ts, P[a][ts]))
    DAY[a] = {k: dict(o=v[0][1]['open'], c=v[-1][1]['close'],
                      h=max(x[1]['high'] for x in v),
                      l=min(x[1]['low'] for x in v)) for k, v in d.items()}
dates = sorted(set().union(*[set(DAY[a]) for a in FX]))
say(f"daily bars: {len(dates)}  {dates[0]} .. {dates[-1]}")

def is_last_bd(d):
    last = calendar.monthrange(d.year, d.month)[1]
    x = dt.date(d.year, d.month, last)
    while x.weekday() >= 5: x -= dt.timedelta(days=1)
    return d == x

def bd_of_month(d):
    n = 0
    for day in range(1, d.day+1):
        x = dt.date(d.year, d.month, day)
        if x.weekday() < 5: n += 1
    return n

say()
say("="*76)
say("1. MONTH-END: is the last business day systematically different?")
say("="*76)
say(f"{'bucket':26s} {'n':>5s} {'mean%':>9s} {'t':>7s} {'WR%':>6s}")
for lab, fn in [
    ('last business day',        lambda d: is_last_bd(d)),
    ('last 2 business days',     lambda d: bd_of_month(d) >= 20 or is_last_bd(d)),
    ('first business day',       lambda d: bd_of_month(d) == 1),
    ('first 3 business days',    lambda d: bd_of_month(d) <= 3),
    ('mid month (bd 8-15)',      lambda d: 8 <= bd_of_month(d) <= 15),
    ('all days',                 lambda d: True)]:
    v = []
    for a in FX:
        for d in dates:
            if d not in DAY[a] or not fn(d): continue
            b = DAY[a][d]
            v.append((b['c']-b['o'])/b['o'])
    if len(v) < 15: continue
    m, t, n = tstat(v)
    say(f"{lab:26s} {n:5d} {m*100:+9.4f} {t:+7.2f} "
        f"{np.mean([x>0 for x in v])*100:6.1f}")

say()
say("="*76)
say("2. QUARTER-END vs ORDINARY MONTH-END (bigger mandated flow)")
say("="*76)
for lab, fn in [
    ('quarter-end last bd', lambda d: is_last_bd(d) and d.month in (3,6,9,12)),
    ('other month-end last bd', lambda d: is_last_bd(d) and d.month not in (3,6,9,12))]:
    v = [(DAY[a][d]['c']-DAY[a][d]['o'])/DAY[a][d]['o']
         for a in FX for d in dates if d in DAY[a] and fn(d)]
    if len(v) < 5: continue
    m, t, n = tstat(v)
    say(f"  {lab:26s} n={n:4d}  mean {m*100:+.4f}%  t={t:+.2f}")

say()
say("="*76)
say("3. DAY OF WEEK -- settlement and funding cycles")
say("="*76)
for wd in range(5):
    v = [(DAY[a][d]['c']-DAY[a][d]['o'])/DAY[a][d]['o']
         for a in FX for d in dates if d in DAY[a] and d.weekday() == wd]
    m, t, n = tstat(v)
    say(f"  {['Mon','Tue','Wed','Thu','Fri'][wd]}  n={n:5d}  "
        f"mean {m*100:+.4f}%  t={t:+6.2f}")

say()
say("="*76)
say("4. HOUR OF DAY -- the London 4pm fix (15:00-16:00 UTC winter)")
say("="*76)
best = []
for hh in range(24):
    v = []
    for a in FX:
        for ts in sorted(P[a]):
            if dt.datetime.utcfromtimestamp(ts).hour != hh: continue
            b = P[a][ts]
            v.append((b['close']-b['open'])/b['open'])
    if len(v) < 100: continue
    m, t, n = tstat(v)
    best.append((abs(t), hh, m, t, n))
best.sort(reverse=True)
for _, hh, m, t, n in best[:6]:
    say(f"  {hh:02d}:00 UTC  n={n:5d}  mean {m*100:+.4f}%  t={t:+6.2f}")
say(f"  (cells searched: {len(best)}, noise max|t| ~ "
    f"{np.sqrt(2*np.log(max(len(best),2))):.2f})")

say()
say("="*76)
say("5. TRADE THE STRONGEST FORCED-FLOW CELL")
say("="*76)
_, hh, m0, t0, n0 = best[0]
pnl = []
for a in FX:
    for ts in sorted(P[a]):
        if dt.datetime.utcfromtimestamp(ts).hour != hh: continue
        b = P[a][ts]
        r = (b['close']-b['open'])/b['open']
        pnl.append(np.sign(m0)*r - 2*SPREAD[a])
m, t, n = tstat(pnl)
say(f"  hour {hh:02d}:00 UTC, {'LONG' if m0>0 else 'SHORT'}, after costs")
say(f"  n={n}  mean {m*100:+.4f}%  t={t:+.2f}  "
    f"WR {np.mean([x>0 for x in pnl])*100:.1f}%  p={signflip_null(pnl):.4f}")
bym = collections.defaultdict(list)
for a in FX:
    for ts in sorted(P[a]):
        if dt.datetime.utcfromtimestamp(ts).hour != hh: continue
        b = P[a][ts]
        bym[dt.datetime.utcfromtimestamp(ts).strftime('%Y-%m')].append(
            np.sign(m0)*(b['close']-b['open'])/b['open'] - 2*SPREAD[a])
sd = float(np.std(pnl, ddof=1))
kmax = 1/abs(min(pnl)) if min(pnl) < 0 else 999
say(f"  worst trade {min(pnl)*100:+.3f}%  -> ruin leverage {kmax:.1f}x")
say(f"\n  {'lev':>7s} {'worst mo%':>11s} {'median mo%':>11s} {'months>500%':>13s}")
for k in (1, 5, 20, round(kmax*0.5,1), round(kmax*0.9,1)):
    mo = []
    for mth in sorted(bym):
        p = 1.0
        for x in bym[mth]:
            s = 1+k*x
            if s <= 0: p = 0; break
            p *= s
        mo.append(p-1)
    say(f"  {k:7.1f} {min(mo)*100:+11.2f} {np.median(mo)*100:+11.2f} "
        f"{sum(1 for v in mo if v>=5.0):>6d}/{len(mo):<6d}")
    if k == round(kmax*0.5,1):
        for mth, v in zip(sorted(bym), mo):
            say(f"        {mth}  {v*100:+10.2f}%")
