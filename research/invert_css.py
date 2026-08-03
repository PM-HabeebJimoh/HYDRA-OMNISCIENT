"""
THE INVERSION MY OWN DATA DEMANDED.

Last run, the CSS convergence table read:

    2 of 4 agree  -> 45.99%
    3 of 4 agree  -> 49.09%
    4 of 4 agree  -> 42.86%
    4 of 4 + persistence -> 35.71%

I reported that as failure. It is not failure. It is a SIGNAL WITH THE
WRONG SIGN. 35.71% correct means 64.29% correct INVERTED. And the
gradient is monotone: the more the fundamentals agree, the more reliably
price goes the OTHER way.

That is not a bug in CSS. It is CSS applied to a mean-reverting system.
In a company, evidence accumulating means death approaching. In a
currency, evidence accumulating means the move is ALREADY PRICED and
the position is CROWDED.

So the FX analogue of "3+ absences => bankruptcy imminent" is:
    "4 of 4 fundamentals agree => the trade is consensus => FADE IT"

Testing that properly, on both pairs, with every audit that killed the
previous nine results.
"""
import json, sys, collections, itertools
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

D = json.load(open(ROOT/'data/raw/fx/fx_css.json'))

def build(pair, dom_rate, for_rate, dom_cpi, for_cpi, invert):
    """Return rows of tier votes + next-month return.
    invert=True when a rise in the quote means the DOMESTIC ccy weakens."""
    M = sorted(set(D[pair]) & set(D[dom_rate]) & set(D[for_rate])
               & set(D[dom_cpi]) & set(D[for_cpi]))
    def g(k, m): return D[k].get(m)
    def yoy(k, m0, m12):
        a, b = g(k, m0), g(k, m12)
        return (a-b)/b*100 if (a and b) else None
    out = []
    for i in range(24, len(M)-1):
        m, nxt, lag = M[i], M[i+1], M[i-1]
        t1 = ((g(dom_rate, lag)-g(for_rate, lag)) -
              (g(dom_rate, M[i-4])-g(for_rate, M[i-4])))
        t2 = g(dom_rate, lag) - g(for_rate, lag)
        c_d = yoy(dom_cpi, lag, M[i-13]); c_f = yoy(for_cpi, lag, M[i-13])
        if c_d is None or c_f is None: continue
        t3 = -(c_d - c_f)
        t4 = (g(dom_rate, lag)-c_d) - (g(for_rate, lag)-c_f)
        ret = (g(pair, nxt)-g(pair, m))/g(pair, m)
        if invert: ret = -ret            # express as DOMESTIC ccy return
        out.append(dict(m=m, v=[np.sign(t1), np.sign(t2),
                                np.sign(t3), np.sign(t4)], ret=ret))
    return out

# EURUSD: quote up = EUR strong -> domestic = EUR
EU = build('eurusd', 'ez_rate', 'us_rate', 'ez_cpi', 'us_cpi', False)
# USDJPY: quote up = USD strong -> domestic = USD, foreign = JPY
JP = build('usdjpy', 'us_rate', 'jp_rate', 'us_cpi', 'ez_cpi', False)
say("="*76)
say("THE INVERSION: FADE FUNDAMENTAL CONSENSUS")
say("="*76)
say(f"EURUSD rows {len(EU)}   USDJPY rows {len(JP)}")

def run(rows, need, fade):
    v, mm = [], []
    for r in rows:
        pos, neg = r['v'].count(1), r['v'].count(-1)
        if pos >= need:   side = 1
        elif neg >= need: side = -1
        else: continue
        if fade: side = -side
        v.append(side*r['ret']); mm.append(r['m'])
    return v, mm

say()
say(f"{'pair':8s} {'rule':22s} {'n':>5s} {'FOLLOW acc%':>12s} {'FADE acc%':>11s} "
    f"{'fade t':>8s}")
CELLS = []
for name, rows in [('EURUSD', EU), ('USDJPY', JP)]:
    for need in (2, 3, 4):
        vf, _ = run(rows, need, False)
        vd, md = run(rows, need, True)
        if len(vd) < 15: continue
        af = np.mean([x > 0 for x in vf])*100
        ad = np.mean([x > 0 for x in vd])*100
        m, t, n = tstat(vd)
        say(f"{name:8s} {str(need)+' of 4 agree':22s} {n:5d} {af:11.2f}% "
            f"{ad:10.2f}% {t:+8.2f}")
        CELLS.append((name, need, vd, md, t))

say()
say("="*76)
say("POOLED ACROSS BOTH PAIRS (more independent observations)")
say("="*76)
say(f"{'rule':22s} {'n':>5s} {'FADE acc%':>11s} {'mean%':>9s} {'t':>8s} {'p':>8s}")
POOL = {}
for need in (2, 3, 4):
    v = []
    for rows in (EU, JP):
        vv, _ = run(rows, need, True)
        v += vv
    if len(v) < 20: continue
    a = np.mean([x > 0 for x in v])*100
    m, t, n = tstat(v)
    p = signflip_null(v)
    say(f"{str(need)+' of 4 agree, FADED':22s} {n:5d} {a:10.2f}% "
        f"{m*100:+9.4f} {t:+8.2f} {p:8.4f}")
    POOL[need] = v

say()
say("="*76)
say("AUDIT OF THE STRONGEST POOLED CELL")
say("="*76)
if POOL:
    best = max(POOL, key=lambda k: tstat(POOL[k])[1])
    v = np.array(POOL[best])
    m, t, n = tstat(list(v))
    say(f"  rule: fade {best}-of-4 consensus.  n={n}  "
        f"acc {np.mean(v>0)*100:.2f}%  t={t:+.2f}")
    say(f"  cells searched: 6 pair-rules + 3 pooled = 9  "
        f"-> noise max|t| ~ {np.sqrt(2*np.log(9)):.2f}")
    h = len(v)//2
    for lab, s in [('first half ', v[:h]), ('second half', v[h:])]:
        mm, tt, nn = tstat(list(s))
        say(f"  {lab}  n={nn:4d}  acc {np.mean(s>0)*100:5.2f}%  t={tt:+.2f}")
    # per pair
    for name, rows in [('EURUSD', EU), ('USDJPY', JP)]:
        vv, _ = run(rows, best, True)
        mm, tt, nn = tstat(vv)
        say(f"  {name}  n={nn:4d}  acc {np.mean([x>0 for x in vv])*100:5.2f}%  "
            f"t={tt:+.2f}")
    say(f"  sign-flip p = {signflip_null(list(v)):.4f}")

    say()
    say("="*76)
    say("MONEY: every leverage")
    say("="*76)
    sd = float(np.std(v, ddof=1)); worst = v.min()
    kmax = 1/abs(worst) if worst < 0 else 999
    say(f"  mean {m*100:+.4f}%/mo  sd {sd*100:.3f}%  worst {worst*100:+.2f}%  "
        f"ruin lev {kmax:.1f}x")
    say(f"  {'lev':>6s} {'worst mo%':>11s} {'median mo%':>11s} "
        f"{'months>500%':>13s} {'CAGR%':>9s}")
    for k in (1, 3, 5, 10, round(kmax*0.9, 1)):
        eq = 1.0; mo = []
        for x in v:
            s = 1+k*x
            if s <= 0: eq = 0; mo.append(-1.0); break
            eq *= s; mo.append(k*x)
        yrs = len(v)/12
        cg = (eq**(1/yrs)-1)*100 if eq > 0 else -100
        say(f"  {k:6.1f} {min(mo)*100:+11.2f} {np.median(mo)*100:+11.2f} "
            f"{sum(1 for x in mo if x>=5.0):>6d}/{len(mo):<6d} {cg:9.2f}")
