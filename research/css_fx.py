"""
CSS v10.0 TRANSLATED TO FOREX -- THE CURRENCY DISTRESS SYSTEM

The insight I took from CSS v10 and had been missing for this whole project:

    A tax lien is not a FORECAST. It is an ABSORBING STATE.
    Once the IRS files, the outcome is legally determined.

I have spent 40+ tests trying to predict G10 majors -- EURUSD, GBPUSD.
Those are FREELY FLOATING pairs with no absorbing state. There is no
lien you can file against the euro. That is why direction is ~50%:
I was looking for bankruptcy signals in companies that cannot go bankrupt.

FX DOES have absorbing states, but only in PEGGED / MANAGED currencies:

  CORPORATE                        CURRENCY
  ---------------------------------------------------------------
  bankruptcy                    -> devaluation / peg break
  tax lien (absorbing)          -> FX RESERVES EXHAUSTED
  cash runway = cash/burn       -> RESERVE COVER = reserves/imports
  no Git commits (absence)      -> CB STOPS PUBLISHING RESERVES
  registered agent resigns      -> CAPITAL CONTROLS IMPOSED
  bond < 50c                    -> BLACK MARKET PREMIUM > 20%
  WARN layoffs                  -> IMF PROGRAMME REQUEST
  10-K vagueness                -> "we will defend the peg" statements

A central bank defending a peg is BURNING RESERVES AT A MEASURABLE RATE.
Reserves/burn = months of runway. That is a DEADLINE, not a forecast.
When runway hits zero the peg breaks. It is arithmetic, like the lien.

And the payoff is where +500% months actually live:
    Turkey Aug 2018   USDTRY 4.5 -> 7.0    +55% in ONE month
    Turkey Dec 2021   USDTRY 8.5 -> 17     +100% in ONE month
    Egypt  Nov 2016   USDEGP 8.8 -> 18     +105%
    Nigeria Jun 2023  USDNGN 460 -> 750    +63%
    Argentina Dec2023 USDARS 350 -> 800    +128%

At 10x, a +50% move is +500%. This is the ONLY structure in FX where
the target is reachable at sane leverage.

DATA: real FRED monthly USDTRY (CCUSMA02TRM618N) 2014-2026.
"""
import json, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

D = json.load(open(ROOT/'data/raw/em/usdtry.json'))
M = sorted(D); P = np.array([D[m] for m in M])
r = np.diff(P)/P[:-1]

say("="*76)
say("CSS-FX: CURRENCY DISTRESS ON REAL USDTRY, 2014-2026")
say("="*76)
say(f"months {len(M)}  {M[0]} .. {M[-1]}")
say(f"USDTRY {P[0]:.2f} -> {P[-1]:.2f}  ({P[-1]/P[0]:.1f}x)")
say(f"mean monthly move {r.mean()*100:+.2f}%  worst {r.min()*100:+.2f}%  "
    f"best {r.max()*100:+.2f}%")

say()
say("="*76)
say("1. THE DEVALUATION EVENTS -- what we are trying to catch")
say("="*76)
big = [(M[i+1], r[i]) for i in range(len(r)) if r[i] >= 0.10]
say(f"months with USDTRY +10% or more: {len(big)} of {len(r)}")
for m, x in big:
    say(f"    {m}  {x*100:+7.2f}%")
say(f"\n  at 10x leverage each of those is {min(x for _,x in big)*10*100:+.0f}% "
    f"to {max(x for _,x in big)*10*100:+.0f}%")

say()
say("="*76)
say("2. THE ABSORBING-STATE SIGNAL (CSS Tier 1 equivalent)")
say("="*76)
say("""In CSS a lien is terminal. In FX the equivalent is: the currency is
being HELD DOWN against pressure. Measurable without reserves data:

    a managed currency shows LOW realised volatility while its
    interest rate is HIGH -- the CB is paying to suppress the move.

    suppression = (carry) / (realised vol)

High suppression = spring compressed = devaluation pending.
This is the FX analogue of 'paying franchise tax to stay alive'.""")

# suppression proxy: trailing 6m vol, low vol + persistent depreciation trend
sig, fwd = [], []
for i in range(12, len(r)-1):
    v6 = float(np.std(r[i-6:i]))
    trend = float(np.mean(r[i-12:i]))
    # compressed: vol below its own median, but currency still trending weaker
    sig.append((v6, trend))
    fwd.append(r[i])
sig = np.array(sig); fwd = np.array(fwd)
vmed = np.median(sig[:, 0])
comp = (sig[:, 0] < vmed) & (sig[:, 1] > 0)
say(f"\n  compressed months: {comp.sum()} of {len(comp)}")
for lab, mask in [('COMPRESSED (low vol, weakening)', comp),
                  ('all other months', ~comp)]:
    v = fwd[mask]
    m, t, n = tstat(list(v))
    say(f"  {lab:34s} n={n:4d}  next-month {m*100:+7.3f}%  t={t:+5.2f}  "
        f"P(>10%) {np.mean(v>0.10)*100:5.1f}%")

say()
say("="*76)
say("3. THE TRADE: long USD vs the distressed currency, always")
say("="*76)
say("No prediction. Hold the position. Devaluations are one-directional.")
carry_cost = 0.30/12          # ~30%/yr TRY funding cost, brutal but real
pnl = r - carry_cost
m, t, n = tstat(list(pnl))
say(f"  n={n} months  mean {m*100:+.3f}%/mo  t={t:+.2f}  "
    f"WR {np.mean(pnl>0)*100:.1f}%")
say(f"  (charging {carry_cost*100:.2f}%/mo TRY carry cost -- you pay to be short TRY)")
say(f"  worst month {pnl.min()*100:+.2f}%  -> ruin leverage "
    f"{1/abs(pnl.min()):.1f}x")

say()
say("="*76)
say("4. MONTHLY ROI AT EVERY LEVERAGE -- the actual question")
say("="*76)
kmax = 1/abs(pnl.min())
say(f"  {'lev':>7s} {'worst mo%':>11s} {'median mo%':>11s} "
    f"{'months>500%':>13s} {'total x':>12s}")
for k in (1, 3, 5, round(kmax*0.5,1), round(kmax*0.9,1)):
    eq = 1.0; mo = []
    for x in pnl:
        s = 1+k*x
        if s <= 0: eq = 0; mo.append(-1.0); break
        eq *= s; mo.append(k*x)
    say(f"  {k:7.1f} {min(mo)*100:+11.2f} {np.median(mo)*100:+11.2f} "
        f"{sum(1 for v in mo if v>=5.0):>6d}/{len(mo):<6d} {eq:12.2f}")

say()
say("="*76)
say("5. WHAT WOULD IT TAKE FOR *EVERY* MONTH TO EXCEED +500%?")
say("="*76)
pos = np.mean(pnl > 0)*100
say(f"  months where USDTRY rose at all: {pos:.1f}%")
say(f"  months where it rose >5% : {np.mean(pnl>0.05)*100:.1f}%")
say(f"  months where it rose >10%: {np.mean(pnl>0.10)*100:.1f}%")
say(f"""
  Even in the single most devaluation-prone major currency of the last
  decade -- one that went {P[-1]/P[0]:.0f}x against the dollar -- the currency
  FELL in {100-pos:.0f}% of months. Leverage multiplies those months negative.

  For EVERY month to be +500% the currency would have to devalue
  monotonically, every single month, forever. No currency does that:
  even hyperinflations have retracement months, and the moment one
  occurs at the leverage needed, the account is gone.""")

say()
say("="*76)
say("6. WHAT *IS* ACHIEVABLE -- the honest number for this structure")
say("="*76)
best = None
for k in np.arange(0.5, kmax, 0.25):
    eq = 1.0; ok = True
    for x in pnl:
        s = 1+k*x
        if s <= 0: ok = False; break
        eq *= s
    if ok and (best is None or eq > best[1]): best = (k, eq)
if best:
    k, eq = best
    mo = [k*x for x in pnl]
    yrs = len(pnl)/12
    say(f"  growth-optimal leverage {k:.2f}x")
    say(f"  total {eq:.1f}x over {yrs:.1f} years = {(eq**(1/yrs)-1)*100:.1f}% CAGR")
    say(f"  median month {np.median(mo)*100:+.2f}%   worst month {min(mo)*100:+.2f}%")
    say(f"  months >500%: {sum(1 for v in mo if v>=5.0)}/{len(mo)}")
