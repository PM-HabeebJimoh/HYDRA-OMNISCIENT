"""
FOREX ONLY. START FROM THE MECHANISM, NOT THE CHART.

The question I never asked: WHAT MECHANICALLY MOVES A CURRENCY PAIR?

An exchange rate is a RELATIVE PRICE OF TWO MONIES. Its value is set by:
  1. RELATIVE PRICE OF MONEY OVER TIME  = interest rate differential
     -> covered interest parity is an ARBITRAGE IDENTITY, not a theory.
        F/S = (1+i_dom)/(1+i_for) holds to the basis, enforced by banks.
        This is the ONLY exactly-known future FX price. It is knowable
        TODAY, before any chart moves.
  2. RELATIVE PRICE OF GOODS         = purchasing power parity (slow anchor)
  3. RELATIVE QUANTITY OF MONEY      = central bank balance sheets
  4. FLOW OF PAYMENTS                = trade / current account

All four are POLICY-SET or ACCOUNTING-DETERMINED, published on a schedule,
and exist entirely OUTSIDE the chart. They are the causes; the chart is
the record.

Data (all real, all FRED, 23.5 years, monthly):
  DEXUSEU  EURUSD spot
  DEXJPUS  USDJPY spot
  DFF      US fed funds
  IRSTCI01EZM156N  euro area policy rate
  IRSTCI01JPM156N  Japan policy rate

Tested: does the rate DIFFERENTIAL -- known before the move -- forecast
the currency? This is the carry trade, the single largest documented
anomaly in FX.
"""
import json, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
from calendar_edge import tstat, signflip_null
def say(*a): print(*a, flush=True)

D = json.load(open(ROOT/'data/raw/fx/fx_macro.json'))
M = sorted(D['eurusd'])
say("="*78)
say("FX FROM FIRST PRINCIPLES: THE RATE DIFFERENTIAL")
say("="*78)
say(f"months: {len(M)}  {M[0]} .. {M[-1]}  ({len(M)/12:.1f} years)")

def ser(k): return {m: D[k].get(m) for m in M}
eur, jpy = ser('eurusd'), ser('usdjpy')
us, ez, jp = ser('us_rate'), ser('ez_rate'), ser('jp_rate')

def ok(m, *ds): return all(d.get(m) is not None for d in ds)

# ---- EURUSD: long EUR earns (ez - us)
say()
say("="*78)
say("TEST 1: DOES THE CARRY (RATE DIFFERENTIAL) PREDICT THE SPOT MOVE?")
say("="*78)
say("Uncovered interest parity says high-rate currencies should DEPRECIATE")
say("by the differential. The documented anomaly is that they APPRECIATE.")
say("Signal known at month start, return realised over the month.")
say()
say(f"{'pair':10s} {'n':>5s} {'corr':>8s} {'t':>7s} {'carry-follow acc%':>18s}")
RES = {}
for name, spot, dom, forn, invert in [
        ('EURUSD', eur, ez, us, False),   # EURUSD up = EUR strong
        ('USDJPY', jpy, us, jp, False)]:  # USDJPY up = USD strong
    rows = []
    for i in range(len(M)-1):
        m, n = M[i], M[i+1]
        if not ok(m, spot, dom, forn) or spot.get(n) is None: continue
        diff = dom[m] - forn[m]                    # KNOWN at month start
        ret = (spot[n]-spot[m])/spot[m]
        rows.append((m, diff, ret))
    d = np.array([r[1] for r in rows]); rr = np.array([r[2] for r in rows])
    c = np.corrcoef(d, rr)[0,1]
    t = c*np.sqrt(len(d)-2)/np.sqrt(1-c**2)
    acc = np.mean(np.sign(d) == np.sign(rr))*100
    say(f"{name:10s} {len(d):5d} {c:+8.4f} {t:+7.2f} {acc:17.2f}%")
    RES[name] = rows

# ---- the carry trade itself: total return = spot + carry
say()
say("="*78)
say("TEST 2: THE CARRY TRADE TOTAL RETURN (spot move + interest earned)")
say("="*78)
say("This is what you actually receive: hold the high-rate currency,")
say("collect the differential monthly, bear the spot move.")
say(f"{'pair':10s} {'n':>5s} {'mean%/mo':>10s} {'sd%':>8s} {'t':>7s} "
    f"{'SR/mo':>7s} {'months+':>9s}")
CARRY = {}
for name, rows in RES.items():
    pnl = []
    for m, diff, ret in rows:
        side = np.sign(diff)                    # long the higher-yielder
        if side == 0: continue
        carry_m = abs(diff)/100/12              # monthly interest earned
        pnl.append(side*ret + carry_m - 0.0002) # 2bp monthly cost
    p = np.array(pnl)
    mm, tt, nn = tstat(list(p))
    sd = float(np.std(p, ddof=1))
    say(f"{name:10s} {nn:5d} {mm*100:+10.4f} {sd*100:8.4f} {tt:+7.2f} "
        f"{mm/sd:7.3f} {np.mean(p>0)*100:8.1f}%")
    CARRY[name] = p

# ---- combined book
say()
say("="*78)
say("TEST 3: COMBINED FX CARRY BOOK -- monthly ROI at every leverage")
say("="*78)
n = min(len(v) for v in CARRY.values())
book = np.mean([v[-n:] for v in CARRY.values()], axis=0)
mm, tt, nn = tstat(list(book))
sd = float(np.std(book, ddof=1))
say(f"  n={nn} months  mean {mm*100:+.4f}%  sd {sd*100:.4f}%  t={tt:+.2f}")
say(f"  monthly Sharpe {mm/sd:.4f}   worst month {book.min()*100:+.2f}%")
kmax = 1/abs(book.min()) if book.min() < 0 else 999
say(f"  ruin leverage k_max = {kmax:.2f}x")
say()
say(f"  {'lev':>6s} {'worst mo%':>11s} {'median mo%':>11s} "
    f"{'months>500%':>13s} {'total x':>12s}")
for k in (1, 2, 5, 10, round(kmax*0.9,1), round(kmax*0.99,1)):
    eq = 1.0; mo = []
    for x in book:
        s = 1+k*x
        if s <= 0: eq = 0; mo.append(-1.0); break
        eq *= s; mo.append(k*x)
    n500 = sum(1 for v in mo if v >= 5.0)
    say(f"  {k:6.1f} {min(mo)*100:+11.2f} {np.median(mo)*100:+11.2f} "
        f"{n500:>6d}/{len(mo):<6d} {eq:12.2f}")

say()
say("="*78)
say("TEST 4: WHY THE CARRY CANNOT GIVE >500% EVERY MONTH")
say("="*78)
say(f"""  The interest differential is a RATE. Over one month you earn
  |i_dom - i_for| / 12. Even a 5 percentage-point differential --
  historically enormous -- pays 5/12 = 0.42% per month.

  To turn 0.42%/month into 500%/month needs leverage of about
  {5.0/0.0042:.0f}x on the carry component alone, while the SPOT component
  has monthly volatility of {np.std([r[2] for r in RES['EURUSD']])*100:.2f}%
  and a worst month of {min(r[2] for r in RES['EURUSD'])*100:.2f}%.

  At {1/abs(min(r[2] for r in RES['EURUSD'])):.0f}x leverage that single month
  is total ruin. The carry is a slow, bounded, arbitrage-anchored return.
  That is exactly WHY it persists: it is too small to arbitrage away.""")
