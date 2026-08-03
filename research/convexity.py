"""
PATH 2: CONVEXITY. Simple. No direction needed.

The claim I made and never tested: gold vol was UNDERPRICED for 8 months
(realised 37.73% vs implied 28.76%). If true, buying convexity pays
regardless of direction.

Simplest possible implementation, no ML, no 84 features:
    Every bar, buy a straddle. Costs money when quiet, pays big when it moves.
    That is long convexity. If vol is underpriced, it wins.

Then the one honest question: does it produce 500%/month?

Everything real. Full decomposition. No untraded bar booked as profit.
"""
import json, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import tstat, signflip_null

def say(*a): print(*a, flush=True)

SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}
p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4); b1 = sorted(p1h)
SUB = collections.defaultdict(list)
for t in b1:
    SUB[t - (t % 14400)].append(t)

def series(a):
    out, pc = [], None
    for t in b4:
        x = p4[t][a]
        out.append((t, x['open'], x['high'], x['low'], x['close'],
                    pc if pc else x['open']))
        pc = x['close']
    return out
S = {a: series(a) for a in A}
N = len(b4)

def straddle(a, i, k):
    """Long convexity: pay a premium = k*ATR, receive |move| at bar end.
    This is the honest payoff of owning a straddle held to expiry.
    Premium is the COST of the position. |move| is what it settles for."""
    q = S[a]
    atr = np.mean([(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)])
    prem = k*atr                      # what you pay to own the convexity
    _, o, h, l, c, _ = q[i+1]
    move = abs(c-o)/o                 # settlement value at expiry
    return move - prem - 2*SPREAD[a]

say("="*74)
say("IS VOLATILITY ACTUALLY UNDERPRICED HERE? (the whole premise)")
say("="*74)
for a in A:
    q = S[a]
    moves, atrs = [], []
    for i in range(21, N-1):
        atr = np.mean([(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i+1)])
        _, o, h, l, c, _ = q[i+1]
        moves.append(abs(c-o)/o); atrs.append(atr)
    moves, atrs = np.array(moves), np.array(atrs)
    ratio = moves.mean()/atrs.mean()
    say(f"  {a:5s} mean |close-open| = {moves.mean()*100:.4f}%   "
        f"mean ATR = {atrs.mean()*100:.4f}%   ratio = {ratio:.3f}")
say("""
  The ratio is the fair strike. If I can buy convexity for LESS than this
  fraction of ATR, long convexity wins. If the market charges MORE, it loses.
  There is no options market in this data, so the honest test is:
  at what premium k does it break even, and is that achievable?""")

say()
say("="*74)
say("BREAK-EVEN PREMIUM, AND WHAT IT COSTS IN REALITY")
say("="*74)
say(f"{'asset':6s} {'k (prem/ATR)':>13s} {'n':>5s} {'mean%':>9s} {'t':>7s} {'WR%':>6s}")
for a in A:
    for k in (0.20, 0.30, 0.40, 0.50, 0.60):
        pnl = [straddle(a, i, k) for i in range(21, N-1)]
        m, t, n = tstat(pnl)
        say(f"  {a:5s} {k:13.2f} {n:5d} {m*100:+9.4f} {t:+7.2f} "
            f"{np.mean([x>0 for x in pnl])*100:6.1f}")
    say("")

say("="*74)
say("THE PROBLEM WITH THIS PATH, STATED PLAINLY")
say("="*74)
say("""
There is no options chain in this dataset. To 'buy convexity' with spot FX
I must synthesise it with a breakout bracket -- and I already measured that
exhaustively:

    4H bracket, worst-case whipsaw, real spreads:
        n=1978  WR 49.34%  mean +0.0394%/trade  t=+2.76  p=0.0020

That IS the convexity trade, done honestly. It is real and it is positive.
Its money value was already computed:

    1.0x  median month  +8.1%   maxDD 21.6%
    2.4x  median month +17.9%   maxDD 45.1%
    4.9x  median month +29.0%   maxDD 72.6%
    9.8x  median month +24.2%   maxDD 95.3%
   15.0x  median month -10.4%   <- growth optimum passed

The growth optimum is ~4.9x at +29%/month. Past that, leverage REDUCES
the median month. That is not a rule I imposed; it is where the Kelly
maximum sits for this edge.
""")

say("="*74)
say("WHAT WOULD 500%/MONTH REQUIRE FROM THIS EDGE?")
say("="*74)
m_tr = 0.000394           # measured mean per trade
n_tr = 130                # trades per month
say(f"  measured edge per trade: {m_tr*100:+.4f}%")
say(f"  trades per month:        {n_tr}")
say(f"  unlevered monthly:       {(np.exp(np.log(1+m_tr)*n_tr)-1)*100:+.2f}%")
need = np.log(6.0)/n_tr
say(f"  need per-trade log-growth of {need:.5f} for 500%/month")
say(f"  at leverage k, growth = k*mu - 0.5*k^2*sigma^2")
sd_tr = 0.0089            # measured per-trade sd from the bracket study
kstar = m_tr/sd_tr**2
gmax = m_tr*kstar - 0.5*kstar**2*sd_tr**2
say(f"  measured per-trade sd:   {sd_tr*100:.3f}%")
say(f"  optimal k* = mu/sigma^2 = {kstar:.2f}")
say(f"  MAXIMUM growth/trade at k*: {gmax:.5f}")
say(f"  MAXIMUM monthly ROI:        {(np.exp(gmax*n_tr)-1)*100:+.2f}%")
say(f"  required:                   +500.00%")
say(f"  shortfall factor:           {need/gmax:.1f}x in log-growth")

say()
say("="*74)
say("THE SINGLE NUMBER THAT ANSWERS EVERYTHING")
say("="*74)
sr_tr = m_tr/sd_tr
sr_mo = sr_tr*np.sqrt(n_tr)
sr_an = sr_tr*np.sqrt(n_tr*12)
say(f"  Sharpe per trade  : {sr_tr:.4f}")
say(f"  Sharpe per month  : {sr_mo:.3f}")
say(f"  Sharpe annualised : {sr_an:.3f}")
say("")
say("  At optimal leverage, max monthly growth = SR_monthly^2 / 2")
say(f"    = {sr_mo:.3f}^2 / 2 = {sr_mo**2/2:.4f}")
say(f"    -> max monthly ROI = {(np.exp(sr_mo**2/2)-1)*100:.2f}%")
say("")
say("  For 500%/month you need SR_monthly = sqrt(2*ln(6)) = "
    f"{np.sqrt(2*np.log(6)):.3f}")
say(f"  i.e. annualised Sharpe = {np.sqrt(2*np.log(6))*np.sqrt(12):.2f}")
say(f"  I measure annualised Sharpe = {sr_an:.2f}")
say("")
say("  Renaissance Medallion runs at annualised Sharpe 3-5.")
say(f"  500%/month every month requires {np.sqrt(2*np.log(6))*np.sqrt(12):.1f}.")
