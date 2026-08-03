"""
FX-CSS: THE CSS v10 *METHOD* APPLIED TO FOREX DIRECTION

What CSS v10 actually does (the lesson, stripped of the domain):

  1. It never predicts from PRICE. Every signal is a non-price fact.
  2. Each signal is INDEPENDENT (tax office, court, GitHub, LinkedIn --
     different institutions that cannot coordinate).
  3. No single signal fires an alert. It requires CONVERGENCE:
     3+ independent signals, or 1 strong + 2 weak.
  4. It requires PERSISTENCE (14-21 days) before acting.
  5. It checks for CONTRADICTION (emergency funding) before firing.
  6. Signals are TIERED by lead time: 365d, 180d, 90d, 30d, 0d.

That is the architecture. Applied to a currency PAIR:

  A currency is strong when, relative to its counterpart:
    TIER 1 (policy, 0-90d lead)   : rates rising faster
    TIER 2 (money, 90-180d lead)  : money supply growing slower
    TIER 3 (prices, 180-365d lead): inflation lower  -> PPP anchor
    TIER 4 (real economy)         : growth stronger, credit healthier

  Every one of those is PUBLISHED, NON-PRICE, and knowable before the
  chart moves. Exactly like a lien filing.

EURUSD is the test pair. All data real, all FRED, monthly, 2003-2026.
Every signal is lagged one month for publication delay.
Walk-forward: thresholds computed from PAST data only.
"""
import json, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

D = json.load(open(ROOT/'data/raw/fx/fx_css.json'))
M = sorted(set(D['eurusd']) & set(D['us_rate']) & set(D['ez_rate'])
           & set(D['us_cpi']) & set(D['ez_cpi']))
say("="*76)
say("FX-CSS: CONVERGENCE OF INDEPENDENT NON-PRICE SIGNALS")
say("="*76)
say(f"months: {len(M)}  {M[0]} .. {M[-1]}  ({len(M)/12:.1f} years)")
say("pair: EURUSD.  All signals published, non-price, lagged 1 month.")

def g(k, m): return D[k].get(m)
def yoy(k, m, i):
    if i < 12: return None
    a, b = g(k, M[i]), g(k, M[i-12])
    return (a-b)/b*100 if (a and b) else None

rows = []
for i in range(24, len(M)-1):
    m, nxt = M[i], M[i+1]
    lag = M[i-1]                                  # publication lag
    # --- TIER 1: policy rate momentum (3m change in differential)
    d_now = g('ez_rate', lag) - g('us_rate', lag)
    d_3m  = g('ez_rate', M[i-4]) - g('us_rate', M[i-4])
    t1 = d_now - d_3m                             # EUR-positive if rising
    # --- TIER 2: rate LEVEL differential (carry -- independent of momentum)
    t2 = g('ez_rate', lag) - g('us_rate', lag)
    # --- TIER 3: inflation differential (EUR strong if EZ inflation lower)
    c_ez, c_us = yoy('ez_cpi', lag, i-1), yoy('us_cpi', lag, i-1)
    t3 = -(c_ez - c_us) if (c_ez is not None and c_us is not None) else None
    # --- TIER 4: real rate differential (level, the fundamental anchor)
    t4 = ((g('ez_rate', lag)-c_ez) - (g('us_rate', lag)-c_us)
          if (c_ez is not None and c_us is not None) else None)
    if None in (t1, t2, t3, t4): continue
    ret = (g('eurusd', nxt)-g('eurusd', m))/g('eurusd', m)
    rows.append(dict(m=m, t1=t1, t2=t2, t3=t3, t4=t4, ret=ret))

say(f"usable months: {len(rows)}")

say()
say("="*76)
say("1. EACH SIGNAL ALONE (CSS: no single signal is an alert)")
say("="*76)
say(f"{'tier':34s} {'acc%':>7s} {'mean%':>8s} {'t':>7s}")
for k, lab in [('t1','T1 policy-rate momentum (0-90d)'),
               ('t2','T2 rate-level carry (0-90d)'),
               ('t3','T3 inflation differential (180d+)'),
               ('t4','T4 real-rate level (anchor)')]:
    v = [np.sign(r[k])*r['ret'] for r in rows if r[k] != 0]
    a = np.mean([np.sign(r[k]) == np.sign(r['ret']) for r in rows if r[k] != 0])*100
    mm, tt, nn = tstat(v)
    say(f"{lab:34s} {a:7.2f} {mm*100:+8.4f} {tt:+7.2f}")

say()
say("="*76)
say("2. CONVERGENCE (the CSS core: require N signals to agree)")
say("="*76)
say("Each tier votes +1 (EUR up) or -1. Count the agreeing votes.")
say(f"{'rule':34s} {'n':>5s} {'acc%':>7s} {'mean%':>8s} {'t':>7s} {'p':>8s}")
CONV = {}
for need in (2, 3, 4):
    v, hits = [], []
    for r in rows:
        votes = [np.sign(r[k]) for k in ('t1','t2','t3','t4')]
        s = sum(votes)
        if abs(s) >= need*2 - 4 + (0 if need < 4 else 0) and abs(s) >= (2*need-4):
            pass
        # require `need` of 4 pointing the same way
        pos, neg = votes.count(1), votes.count(-1)
        if pos >= need:   side = 1
        elif neg >= need: side = -1
        else: continue
        v.append(side*r['ret']); hits.append((r['m'], side, r['ret']))
    if len(v) < 20: continue
    a = np.mean([x > 0 for x in v])*100
    mm, tt, nn = tstat(v)
    p = signflip_null(v)
    say(f"{'require '+str(need)+' of 4 tiers agree':34s} {nn:5d} {a:7.2f} "
        f"{mm*100:+8.4f} {tt:+7.2f} {p:8.4f}")
    CONV[need] = (v, hits)

say()
say("="*76)
say("3. UNANIMOUS CONVERGENCE + PERSISTENCE (full CSS protocol)")
say("="*76)
say("CSS requires the state to PERSIST before firing. Same here:")
say("all 4 tiers agree, AND agreed the same way last month.")
prev = {}
v, hits = [], []
for idx, r in enumerate(rows):
    votes = [np.sign(r[k]) for k in ('t1','t2','t3','t4')]
    side = 1 if votes.count(1) == 4 else (-1 if votes.count(-1) == 4 else 0)
    if side and prev.get('side') == side:
        v.append(side*r['ret']); hits.append((r['m'], side, r['ret']))
    prev['side'] = side
if v:
    a = np.mean([x > 0 for x in v])*100
    mm, tt, nn = tstat(v)
    say(f"  n={nn}  accuracy {a:.2f}%  mean {mm*100:+.4f}%  t={tt:+.2f}  "
        f"p={signflip_null(v):.4f}")
    say(f"  signals per year: {nn/(len(rows)/12):.1f}")
else:
    say("  no unanimous+persistent signals")

say()
say("="*76)
say("4. THE MONEY -- best convergence rule, every leverage")
say("="*76)
best_need = max(CONV, key=lambda k: tstat(CONV[k][0])[1]) if CONV else None
if best_need:
    v, hits = CONV[best_need]
    a = np.mean([x > 0 for x in v])*100
    mm, tt, nn = tstat(v)
    say(f"  rule: {best_need} of 4 tiers agree.  acc {a:.2f}%  t={tt:+.2f}  n={nn}")
    bym = collections.defaultdict(list)
    for (mth, side, ret), pv in zip(hits, v): bym[mth[:7]].append(pv)
    worst = min(v); kmax = 1/abs(worst) if worst < 0 else 999
    say(f"  worst month {worst*100:+.2f}%  -> ruin leverage {kmax:.1f}x")
    say(f"\n  {'lev':>6s} {'worst mo%':>11s} {'median mo%':>11s} "
        f"{'months>500%':>13s} {'CAGR%':>9s}")
    for k in (1, 3, 5, 10, round(kmax*0.9,1)):
        eq = 1.0; mo = []
        for x in v:
            s = 1+k*x
            if s <= 0: eq = 0; mo.append(-1.0); break
            eq *= s; mo.append(k*x)
        yrs = len(v)/12
        cg = (eq**(1/yrs)-1)*100 if eq > 0 else -100
        say(f"  {k:6.1f} {min(mo)*100:+11.2f} {np.median(mo)*100:+11.2f} "
            f"{sum(1 for x in mo if x>=5.0):>6d}/{len(mo):<6d} {cg:9.2f}")

say()
say("="*76)
say("5. WHY CSS WORKS FOR COMPANIES AND NOT FOR FX -- the structural test")
say("="*76)
say("""CSS predicts an ABSORBING STATE (bankruptcy): once entered, never left.
A currency has NO absorbing state -- EURUSD at 1.05 can go to 1.20 and back.

Concretely: CSS signals are one-directional (a lien is never 'un-filed').
FX signals MEAN-REVERT. Test: does the sign of each tier persist?""")
for k, lab in [('t1','T1 policy'), ('t2','T2 carry'),
               ('t3','T3 inflation'), ('t4','T4 real rate')]:
    s = [np.sign(r[k]) for r in rows]
    flips = sum(1 for i in range(1, len(s)) if s[i] != s[i-1])
    say(f"  {lab:14s} sign flips {flips:3d} times in {len(s)} months "
        f"({flips/len(s)*100:.1f}% of months)")
say("""
  A tax lien flips 0% of the time. These flip constantly.
  That is the structural difference, measured -- not asserted.""")
