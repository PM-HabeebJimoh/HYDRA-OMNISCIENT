"""
VALIDATE THE 72.94% POCKET.

Found: "event_bar AND up_bar AND NOT vol_expand" -> 72.94% next-bar up, n=85,
z=+4.23 against a multiple-testing threshold of 4.06. First cell in this
entire project to exceed its own noise expectation.

If real, the arithmetic is decisive:
    p=0.7294, 1:1 payoff -> Kelly f* = 0.459
    growth/trade = 0.7294*ln(1.459) + 0.2706*ln(0.541) = 0.1101
    but only ~11 signals/month (85 over 7.8 months)
    -> monthly ROI = exp(0.1101*11) - 1 = +235%

So this cell alone would be worth +235%/month if it holds. It must now
survive every test that killed the previous nine.
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

def say(*a): print(*a, flush=True)
SPREAD = {'gold':0.00012,'eur':0.000045,'aud':0.000075}

p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4); b1 = sorted(p1h)
SUB = collections.defaultdict(list)
for t in b1: SUB[t-(t%14400)].append(t)
EV = build_events()
sched = collections.Counter(e['ts']-(e['ts']%14400) for e in EV)
S = {}
for a in A:
    out, pc = [], None
    for t in b4:
        x = p4[t][a]
        out.append((t,x['open'],x['high'],x['low'],x['close'],pc if pc else x['open']))
        pc = x['close']
    S[a] = out
N = len(b4)

def signal(a, i):
    """event_bar AND up_bar AND NOT vol_expand -- all causal at bar i."""
    q = S[a]; t = q[i][0]
    _, o, h, l, c, pc = q[i]
    rr = [(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i)]
    atr, atr5 = np.mean(rr), np.mean(rr[-5:])
    return (sched.get(t,0) >= 1) and (c > o) and not (atr5 > atr*1.2)

hits = [(a,i) for a in A for i in range(25,N-1) if signal(a,i)]
y = np.array([1 if S[a][i+1][4] > S[a][i+1][1] else 0 for a,i in hits])
say("="*76)
say("1. REPRODUCE THE CELL")
say("="*76)
say(f"  n={len(y)}  accuracy {y.mean()*100:.2f}%  "
    f"z={(y.mean()*100-50)/(np.sqrt(0.25/len(y))*100):+.2f}")

say()
say("="*76)
say("2. SPLIT-HALF IN TIME  <- the test that killed COT")
say("="*76)
h = len(y)//2
for lab, s in [('first half ', y[:h]), ('second half', y[h:])]:
    z = (s.mean()*100-50)/(np.sqrt(0.25/len(s))*100)
    say(f"  {lab}  n={len(s):3d}  acc {s.mean()*100:5.2f}%  z={z:+.2f}")

say()
say("="*76)
say("3. PER-ASSET  <- does it depend on one instrument?")
say("="*76)
for a in A:
    sub = [1 if S[a][i+1][4] > S[a][i+1][1] else 0
           for aa,i in hits if aa == a]
    if len(sub) < 10: continue
    s = np.array(sub)
    z = (s.mean()*100-50)/(np.sqrt(0.25/len(s))*100)
    say(f"  {a:5s} n={len(s):3d}  acc {s.mean()*100:5.2f}%  z={z:+.2f}")

say()
say("="*76)
say("4. MONTH BY MONTH  <- is it one lucky month?")
say("="*76)
bym = collections.defaultdict(list)
for (a,i), v in zip(hits, y):
    bym[dt.datetime.utcfromtimestamp(S[a][i][0]).strftime('%Y-%m')].append(v)
for k in sorted(bym):
    s = np.array(bym[k])
    say(f"  {k}  n={len(s):3d}  acc {s.mean()*100:5.1f}%")
say(f"  months above 50%: {sum(1 for v in bym.values() if np.mean(v)>0.5)}"
    f"/{len(bym)}")

say()
say("="*76)
say("5. IS IT JUST 'UP BARS FOLLOW UP BARS'? -- the control")
say("="*76)
for lab, fn in [
    ('up_bar only',
     lambda a,i: S[a][i][4] > S[a][i][1]),
    ('event_bar only',
     lambda a,i: sched.get(S[a][i][0],0) >= 1),
    ('up_bar AND NOT vol_expand',
     lambda a,i: S[a][i][4] > S[a][i][1] and not (
         np.mean([(S[a][j][2]-S[a][j][3])/S[a][j][1] for j in range(i-5,i)]) >
         np.mean([(S[a][j][2]-S[a][j][3])/S[a][j][1] for j in range(i-20,i)])*1.2)),
    ('FULL POCKET', signal),
]:
    hh = [(a,i) for a in A for i in range(25,N-1) if fn(a,i)]
    if len(hh) < 20: continue
    yy = np.array([1 if S[a][i+1][4] > S[a][i+1][1] else 0 for a,i in hh])
    z = (yy.mean()*100-50)/(np.sqrt(0.25/len(yy))*100)
    say(f"  {lab:28s} n={len(yy):4d}  acc {yy.mean()*100:5.2f}%  z={z:+.2f}")

say()
say("="*76)
say("6. TRADE IT ON THE REAL 1H PATH  <- the test that killed asymmetry")
say("="*76)
say("  close-vs-open accuracy is NOT tradeable accuracy.")
def path_trade(a, i, stop_m, targ_m):
    q = S[a]
    atr = np.mean([(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i)])
    tb = q[i+1][0]; subs = SUB.get(tb, [])
    if len(subs) < 2 or not atr: return None
    o = p1h[subs[0]][a]['open']; hs = SPREAD[a]
    tp, sl = o*(1+targ_m*atr), o*(1-stop_m*atr)
    for t in subs:
        b = p1h[t][a]
        if b['high'] >= tp and b['low'] <= sl: return -stop_m*atr - 2*hs
        if b['low'] <= sl: return -stop_m*atr - 2*hs
        if b['high'] >= tp: return targ_m*atr - 2*hs
    return (p1h[subs[-1]][a]['close']-o)/o - 2*hs

say(f"  {'stop':>6s} {'targ':>6s} {'n':>5s} {'WR%':>6s} {'mean%':>9s} {'t':>7s}")
best = None
for sm, tm in [(0.5,0.5),(0.5,1.0),(1.0,1.0),(1.0,2.0),(2.0,1.0)]:
    pnl = [v for a,i in hits if (v := path_trade(a,i,sm,tm)) is not None]
    if len(pnl) < 20: continue
    m,t,n = tstat(pnl)
    wr = np.mean([x>0 for x in pnl])*100
    say(f"  {sm:6.2f} {tm:6.2f} {n:5d} {wr:6.1f} {m*100:+9.4f} {t:+7.2f}")
    if best is None or m > best[0]: best = (m,t,n,wr,sm,tm,pnl)

say()
say("="*76)
say("7. VERDICT AND MONEY")
say("="*76)
if best:
    m,t,n,wr,sm,tm,pnl = best
    say(f"  best geometry stop{sm} targ{tm}: WR {wr:.1f}%  mean {m*100:+.4f}%  t={t:+.2f}")
    say(f"  sign-flip p = {signflip_null(pnl):.4f}")
    sd = float(np.std(pnl, ddof=1))
    if m > 0 and sd > 0:
        k = m/sd**2
        gk = m*k - 0.5*k*k*sd*sd
        per_mo = n/7.8
        say(f"  signals/month {per_mo:.1f}   k* = {k:.2f}")
        say(f"  max monthly ROI = exp({gk:.5f}*{per_mo:.1f})-1 = "
            f"{(np.exp(gk*per_mo)-1)*100:+.2f}%")
    else:
        say(f"  mean <= 0 : NOT TRADEABLE. Kelly f* <= 0.")
    say(f"\n  close-vs-open accuracy : 72.94%")
    say(f"  path-traded win rate   : {wr:.1f}%")
