"""
10-YEAR BACKTEST. GOAL: >500% ROI EVERY MONTH, CONSTANT.

Data: 23.5 years of real monthly gold (FRED IQ12260) + 6.7 years of real
weekly gold (Investing.com). Every leverage from 1x to the ruin limit.

The test is simple and has one pass/fail criterion:
    is the WORST month of the backtest above +500%?
"""
import json, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
def say(*a): print(*a, flush=True)

# ---------- real monthly gold, 23.5 years
D = json.load(open(ROOT/'data/raw/long/monthly.json'))
g = D['gold']; ms = sorted(g); G = np.array([g[k] for k in ms])
r = np.diff(G)/G[:-1]
say("="*76)
say("10-YEAR+ BACKTEST ON REAL DATA")
say("="*76)
say(f"gold monthly returns: n={len(r)}  {ms[0]} .. {ms[-1]}  "
    f"({len(r)/12:.1f} years)")
say(f"index {G[0]:.1f} -> {G[-1]:.1f} = {G[-1]/G[0]:.2f}x")
say(f"mean {r.mean()*100:+.3f}%/mo  sd {r.std()*100:.3f}%  "
    f"up-months {np.mean(r>0)*100:.1f}%")

# ---------- what would +500% every month even mean
say()
say("="*76)
say("STEP 0: WHAT DOES '+500% EVERY MONTH FOR 10 YEARS' REQUIRE?")
say("="*76)
say("  +500% per month = 6x per month")
for yrs in (1, 5, 10):
    n = yrs*12
    say(f"  {yrs:2d} years = {n:3d} months -> 6^{n} = 10^{n*np.log10(6):.0f}x")
say(f"\n  Starting from $10,000, after 10 years: "
    f"$10,000 x 10^{120*np.log10(6):.0f}")
say(f"  Total money on Earth is about 10^14 dollars.")
say(f"  The requirement exceeds it by a factor of 10^{120*np.log10(6)-10:.0f}.")

# ---------- run every leverage on the real path
say()
say("="*76)
say("STEP 1: EVERY LEVERAGE ON 23.5 YEARS OF REAL GOLD")
say("="*76)
say(f"{'lev':>6s} {'worst mo%':>11s} {'median mo%':>11s} "
    f"{'months>500%':>12s} {'CAGR%':>10s} {'ruin?':>7s}")
for k in (1, 2, 3, 5, 8, 10, 15, 20, 24):
    eq, mo, ruin = 1.0, [], False
    for x in r:
        step = 1 + k*x
        if step <= 0:
            ruin = True; mo.append(-1.0); break
        eq *= step; mo.append(k*x)
    yrs = len(r)/12
    cagr = (eq**(1/yrs)-1)*100 if eq > 0 and not ruin else -100
    n500 = sum(1 for m in mo if m >= 5.0)
    say(f"{k:6d} {min(mo)*100:+11.2f} {np.median(mo)*100:+11.2f} "
        f"{n500:>6d}/{len(mo):<5d} {cagr:10.2f} {'RUIN' if ruin else '':>7s}")

# ---------- the ruin boundary
worst = r.min()
kmax = 1/abs(worst)
say(f"\n  worst single month in 23.5 years: {worst*100:+.2f}%")
say(f"  => ruin leverage k_max = 1/{abs(worst)*100:.2f}% = {kmax:.2f}x")
say(f"  Any k >= {kmax:.2f} wipes the account to zero on that one month.")

# ---------- best possible: perfect hindsight leverage per month
say()
say("="*76)
say("STEP 2: PERFECT HINDSIGHT -- pick the best k for EVERY month")
say("="*76)
say("  Impossible in practice. This is the mathematical ceiling.")
n500 = 0; worstm = 1e9
for x in r:
    # with hindsight, if month is up you use kmax, if down you use 0
    best = max(0.0, kmax*0.999*x) if x > 0 else 0.0
    n500 += 1 if best >= 5.0 else 0
    worstm = min(worstm, best)
say(f"  months reaching +500% with perfect hindsight: {n500}/{len(r)}")
say(f"  worst month with perfect hindsight: {worstm*100:+.2f}%")
say(f"  (a flat/down month gives 0% no matter what leverage you pick,")
say(f"   because you cannot lever a non-existent move)")

# ---------- weekly data, higher frequency = more compounding
say()
say("="*76)
say("STEP 3: WEEKLY DATA (more compounding events per month)")
say("="*76)
W = json.load(open(ROOT/'data/raw/oos/gold_weekly.json'))
wt = [dt.date.fromtimestamp(t) for t in W['t']]; wc = np.array(W['c'])
wr = np.diff(wc)/wc[:-1]
say(f"weekly returns n={len(wr)}  {wt[0]} .. {wt[-1]}")
say(f"mean {wr.mean()*100:+.4f}%/wk  sd {wr.std()*100:.3f}%  "
    f"worst {wr.min()*100:+.2f}%")
kmax_w = 1/abs(wr.min())
say(f"ruin leverage on weekly: {kmax_w:.2f}x")
bym = collections.defaultdict(list)
for d, x in zip(wt[1:], wr):
    bym[d.strftime('%Y-%m')].append(x)
say(f"\n{'lev':>6s} {'worst mo%':>11s} {'median mo%':>11s} {'months>500%':>13s}")
for k in (1, 5, 10, 20, round(kmax_w*0.9, 1)):
    mo = []
    for mth in sorted(bym):
        p = 1.0
        for x in bym[mth]:
            s = 1 + k*x
            if s <= 0: p = 0.0; break
            p *= s
        mo.append(p - 1)
    n500 = sum(1 for m in mo if m >= 5.0)
    say(f"{k:6.1f} {min(mo)*100:+11.2f} {np.median(mo)*100:+11.2f} "
        f"{n500:>6d}/{len(mo):<6d}")

say()
say("="*76)
say("RESULT")
say("="*76)
say("""  Across 23.5 years of monthly data and 6.7 years of weekly data,
  at every leverage from 1x to the ruin boundary, including a
  perfect-hindsight run that cheats:

      NO configuration produces >500% in even half the months,
      and NONE produces it in EVERY month.

  The reason is arithmetic, not opinion:
    * gold falls in ~43% of months
    * leverage multiplies a negative month into a worse negative month
    * a month that is flat or down cannot be levered into +500%
    * the ruin boundary caps k at 1/|worst month|""")
