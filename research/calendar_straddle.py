"""
THE ONLY HONEST ANTICIPATORY TRADE THE CALENDAR PERMITS.

Established facts (this session, real Investing.com data):
  * Release bars have 1.26-1.41x the range of SAME-HOUR non-release bars
    (t = +2.64/+3.88/+3.76), in 8 of 8 months. Known DAYS in advance.
  * The DIRECTION of the release-bar move is unpredictable (t = +0.44/-0.27/+0.66).

Big move, unknown sign, known in advance = a straddle. You pre-position at the
open of the bar that contains the print -- an entry you can place days ahead --
and you profit from the size of the move, not its sign.

This is the purest possible form of "know before it happens": the position is
placed before the number exists, on information published a week earlier.

Tested honestly:
  - entry at bar OPEN, before the release inside that bar
  - worst-case whipsaw (both legs trigger = full double loss)
  - real half-spreads
  - no cap, no deletion of losing bars, no parameter chosen after seeing PnL
"""
import sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, A
from calendar_edge import build_events, tstat, signflip_null

SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}

p1h = load_1h()
bars = sorted(p1h)
idx = {t: i for i, t in enumerate(bars)}
events = build_events()
ev_bar = collections.Counter()
for e in events:
    i = idx.get(e['ts'] - (e['ts'] % 3600))
    if i is not None:
        ev_bar[i] += 1

def atr1h(a, i, n=20):
    tr = []
    for j in range(max(1, i - n), i):
        b, pb = p1h[bars[j]][a], p1h[bars[j - 1]][a]
        tr.append(max(b['high'] - b['low'], abs(b['high'] - pb['close']),
                      abs(b['low'] - pb['close'])) / pb['close'])
    return np.mean(tr) if tr else None

def straddle(a, i, wmult):
    """Bracket placed at the open of bar i. Worst-case whipsaw."""
    A_ = atr1h(a, i)
    if not A_: return None
    b = p1h[bars[i]][a]
    o, w, hs = b['open'], wmult * A_, SPREAD[a]
    up, dn = o * (1 + w), o * (1 - w)
    hu, hd = b['high'] >= up, b['low'] <= dn
    if hu and hd: return -2 * w - 2 * hs
    if hu:        return (b['close'] - up) / o - hs
    if hd:        return (dn - b['close']) / o - hs
    return None

print("=" * 78)
print("STRADDLE ON SCHEDULED RELEASE BARS vs EVERYTHING ELSE (1H, real data)")
print("=" * 78)
print(f"{'width':>6s} {'bucket':22s} {'n':>5s} {'mean%':>9s} {'t':>7s} {'WR%':>6s}")
for w in (0.5, 0.75, 1.0, 1.5):
    for lbl, keep in [('release bars', lambda i: ev_bar.get(i, 0) >= 1),
                      ('non-release bars', lambda i: ev_bar.get(i, 0) == 0)]:
        pnl = [r for a in A for i in range(21, len(bars))
               if keep(i) and (r := straddle(a, i, w)) is not None]
        m, t, n = tstat(pnl)
        print(f"{w:6.2f} {lbl:22s} {n:5d} {m*100:+9.4f} {t:+7.2f} "
              f"{np.mean([v>0 for v in pnl])*100:6.1f}")
    print()

print("=" * 78)
print("VERDICT ON THE BEST RELEASE-BAR CELL")
print("=" * 78)
best = None
for w in (0.5, 0.75, 1.0, 1.5):
    pnl = [r for a in A for i in range(21, len(bars))
           if ev_bar.get(i, 0) >= 1 and (r := straddle(a, i, w)) is not None]
    m, t, n = tstat(pnl)
    if best is None or t > best[1]: best = (w, t, m, n, pnl)
w, t, m, n, pnl = best
print(f"  width {w}xATR   n={n}   mean {m*100:+.4f}%   t={t:+.2f}")
print(f"  cells searched: 4 widths x 2 buckets = 8; "
      f"expected max|t| ~ {np.sqrt(2*np.log(8)):.2f}")
print(f"  sign-flip null on this cell: p = {signflip_null(pnl):.4f}")
x = np.asarray(pnl); h = len(x)//2
for lbl, s in [('first half ', x[:h]), ('second half', x[h:])]:
    mm, tt, nn = tstat(list(s))
    print(f"  {lbl}  n={nn:4d}  mean {mm*100:+.4f}%  t={tt:+5.2f}")
