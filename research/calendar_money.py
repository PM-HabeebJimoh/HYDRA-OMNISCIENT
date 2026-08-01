"""
What is the calendar layer actually worth, in money, honestly?

Combines the one verified anticipatory signal (scheduled releases predict
range, known days ahead, 8/8 months, hour-matched t=+2.6..+3.9) with the
prior session's verified 4H magnitude bet, and reports WR / monthly ROI / DD
across leverage -- the user's three numbers.
"""
import sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events, tstat, signflip_null

SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}
p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4)
events = build_events()
sched = collections.Counter(e['ts'] - (e['ts'] % 14400) for e in events)

def series(a):
    out, pc = [], None
    for t in b4:
        d = p4[t][a]
        out.append(dict(t=t, o=d['open'], h=d['high'], l=d['low'], c=d['close'],
                        pc=pc if pc else d['open']))
        pc = d['close']
    return out

def atr(s, i, n=20):
    tr = [max(s[j]['h']-s[j]['l'], abs(s[j]['h']-s[j]['pc']),
              abs(s[j]['l']-s[j]['pc']))/s[j]['pc'] for j in range(max(0,i-n), i)]
    return np.mean(tr) if tr else None

def trades(hold=3, w=1.0):
    """Verified 4H bracket, hold `hold` bars, worst-case whipsaw."""
    out = []
    for a in A:
        s = series(a)
        for i in range(21, len(s)-hold):
            A_ = atr(s, i)
            if not A_: continue
            o, hs = s[i]['o'], SPREAD[a]
            up, dn = o*(1+w*A_), o*(1-w*A_)
            hu, hd = s[i]['h'] >= up, s[i]['l'] <= dn
            if hu and hd:
                r = -2*w*A_ - 2*hs
            elif hu:
                r = (s[i+hold]['c'] - up)/o - hs
            elif hd:
                r = (dn - s[i+hold]['c'])/o - hs
            else:
                continue
            out.append((s[i]['t'], a, r, sched.get(s[i]['t'], 0)))
    return sorted(out)

T = trades()
print("=" * 78)
print("VERIFIED 4H BRACKET, SPLIT BY THE CALENDAR (known days ahead)")
print("=" * 78)
for lbl, keep in [('ALL',            lambda k: True),
                  ('calendar QUIET', lambda k: k == 0),
                  ('calendar BUSY',  lambda k: k >= 1)]:
    p = [r for _, _, r, k in T if keep(k)]
    m, t, n = tstat(p)
    print(f"  {lbl:16s} n={n:5d}  mean {m*100:+.4f}%  t={t:+5.2f}  "
          f"WR {np.mean([v>0 for v in p])*100:.1f}%")

print()
print("=" * 78)
print("MONEY: equity curve, per-bar concurrency handled (3 assets share equity)")
print("=" * 78)
byt = collections.defaultdict(list)
for t_, a, r, k in T:
    byt[t_].append(r)
times = sorted(byt)
print(f"{'lev':>5s} {'WR%':>6s} {'median mo%':>11s} {'worst mo%':>10s} "
      f"{'maxDD%':>8s} {'8-mo total%':>12s}")
for lev in (1.0, 2.0, 4.0, 8.0, 12.0):
    eq, peak, dd = 1.0, 1.0, 0.0
    curve, wins, tot = {}, 0, 0
    for t_ in times:
        rs = byt[t_]
        step = lev * np.mean(rs)          # equal split across concurrent legs
        eq *= (1 + step)
        wins += sum(1 for r in rs if r > 0); tot += len(rs)
        peak = max(peak, eq); dd = max(dd, 1 - eq/peak)
        curve[dt.datetime.utcfromtimestamp(t_).strftime('%Y-%m')] = eq
        if eq <= 0: break
    mk = sorted(curve)
    mret, prev = [], 1.0
    for k in mk:
        mret.append(curve[k]/prev - 1); prev = curve[k]
    print(f"{lev:5.1f} {wins/tot*100:6.1f} {np.median(mret)*100:+11.2f} "
          f"{min(mret)*100:+10.2f} {dd*100:8.2f} {(eq-1)*100:+12.2f}")

print()
print("=" * 78)
print("SAME, BUT ONLY TRADING CALENDAR-BUSY BARS")
print("=" * 78)
byt2 = collections.defaultdict(list)
for t_, a, r, k in T:
    if k >= 1: byt2[t_].append(r)
times2 = sorted(byt2)
print(f"  tradeable 4H bars: {len(times2)} of {len(times)} "
      f"({len(times2)/len(times)*100:.0f}%)")
print(f"{'lev':>5s} {'WR%':>6s} {'median mo%':>11s} {'worst mo%':>10s} "
      f"{'maxDD%':>8s} {'8-mo total%':>12s}")
for lev in (1.0, 2.0, 4.0, 8.0, 12.0):
    eq, peak, dd = 1.0, 1.0, 0.0
    curve, wins, tot = {}, 0, 0
    for t_ in times2:
        rs = byt2[t_]
        eq *= (1 + lev*np.mean(rs))
        wins += sum(1 for r in rs if r > 0); tot += len(rs)
        peak = max(peak, eq); dd = max(dd, 1 - eq/peak)
        curve[dt.datetime.utcfromtimestamp(t_).strftime('%Y-%m')] = eq
        if eq <= 0: break
    mk = sorted(curve); mret, prev = [], 1.0
    for k in mk:
        mret.append(curve[k]/prev - 1); prev = curve[k]
    print(f"{lev:5.1f} {wins/tot*100:6.1f} {np.median(mret)*100:+11.2f} "
          f"{min(mret)*100:+10.2f} {dd*100:8.2f} {(eq-1)*100:+12.2f}")
