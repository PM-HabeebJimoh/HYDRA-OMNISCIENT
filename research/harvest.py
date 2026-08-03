"""
REPLACEMENT: STOP PREDICTING. HARVEST.

Every framing so far assumed returns come from PREDICTION. That assumption is
the actual limiting factor, and I never questioned it.

There is a return source that requires ZERO directional accuracy:

    THE REBALANCING PREMIUM (Shannon's Demon / volatility harvesting)

For a periodically rebalanced portfolio the geometric growth rate is

    g = w'mu  -  (1/2) w'Sigma w        [portfolio]
    vs sum of  w_i*(mu_i - (1/2)sigma_i^2)   [buy and hold]

The DIFFERENCE is  (1/2)( sum w_i sigma_i^2  -  w'Sigma w )  >= 0 always,
and it is LARGER when:
      * individual variances are LARGE
      * cross-correlations are LOW

It is a pure function of VOLATILITY and CORRELATION. It contains no mu.
It needs no forecast of direction at all.

And here is why this is not a generic idea: the term that drives it is
sigma^2 -- the one quantity this project can forecast, at IC ~0.50, t=+17.
My magnitude edge has a direct monetisation path that never touches direction.

Tested here, all real data, all costs charged:
  1. Does the premium exist in these assets, measured not assumed?
  2. Does rebalancing beat buy-and-hold after real spreads?
  3. Does TIMING the rebalance with my volatility forecast beat fixed-interval?
  4. Full decomposition -- which line of code produced every basis point.
"""
import json, sys, glob, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import tstat, signflip_null

def say(*a): print(*a, flush=True)

SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}

p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4)
say(f"4H bars {len(b4)}  {dt.datetime.utcfromtimestamp(b4[0]):%Y-%m-%d} .. "
    f"{dt.datetime.utcfromtimestamp(b4[-1]):%Y-%m-%d}")

# ---- returns matrix
R = {a: [] for a in A}
for k in range(1, len(b4)):
    for a in A:
        prev, cur = p4[b4[k-1]][a]['close'], p4[b4[k]][a]['close']
        R[a].append((cur - prev) / prev)
M = np.array([R[a] for a in A])          # 3 x T
T = M.shape[1]
say(f"return matrix {M.shape}")

say()
say("="*78)
say("1. THE INGREDIENTS -- measured, not assumed")
say("="*78)
sd = M.std(axis=1)
C = np.corrcoef(M)
for i, a in enumerate(A):
    say(f"  {a:5s} per-bar sigma {sd[i]*100:.4f}%   "
        f"annualised {sd[i]*np.sqrt(6*252)*100:5.1f}%   "
        f"mean {M[i].mean()*100:+.5f}%")
say(f"  correlations: gold/eur {C[0,1]:+.3f}  gold/aud {C[0,2]:+.3f}  "
    f"eur/aud {C[1,2]:+.3f}")
w = np.ones(3)/3
Sig = np.cov(M)
gross = 0.5*(np.sum(w*np.diag(Sig)) - w @ Sig @ w)
say(f"\n  THEORETICAL rebalancing premium per bar = "
    f"0.5*(sum w_i s_i^2 - w'Sw) = {gross*100:.6f}%")
say(f"  per month (~130 bars): {gross*130*100:.4f}%")
say(f"  -> this is the entire prize. Everything else is execution cost.")

say()
say("="*78)
say("2. DOES IT SURVIVE REAL COSTS? measured, decomposed")
say("="*78)
say("Rebalancing to equal weight requires trading. Charge the real spread")
say("on every unit of turnover. Compare against never rebalancing.")

def run(freq, cost_on=True, label=''):
    """Equal-weight, rebalance every `freq` bars. Returns dict of components."""
    wts = np.ones(3)/3
    eq = 1.0
    turn_total = 0.0
    cost_total = 0.0
    curve = []
    for t in range(T):
        r = M[:, t]
        # portfolio return with current weights
        pr = float(wts @ r)
        eq *= (1 + pr)
        # drift the weights
        wts = wts*(1+r)
        wts = wts/wts.sum()
        if (t+1) % freq == 0:
            tgt = np.ones(3)/3
            turn = float(np.abs(wts - tgt).sum())/2      # one-way turnover
            cost = turn * float(np.mean(list(SPREAD.values())))*2 if cost_on else 0.0
            eq *= (1 - cost)
            turn_total += turn; cost_total += cost
            wts = tgt
        curve.append(eq)
    return dict(eq=eq, curve=np.array(curve), turn=turn_total, cost=cost_total)

# buy and hold (never rebalance)
bh = run(10**9, cost_on=False, label='B&H')
say(f"{'strategy':22s} {'final eq':>10s} {'vs B&H':>9s} {'turnover':>10s} "
    f"{'cost paid':>10s}")
say(f"{'buy & hold (no rebal)':22s} {bh['eq']:10.5f} {'--':>9s} "
    f"{0.0:10.2f} {0.0:10.4f}")
best = None
for f in (1, 2, 6, 12, 30, 60, 130):
    r = run(f)
    d = r['eq'] - bh['eq']
    say(f"{'rebalance every '+str(f)+'b':22s} {r['eq']:10.5f} {d:+9.5f} "
        f"{r['turn']:10.2f} {r['cost']*100:9.3f}%")
    if best is None or d > best[1]:
        best = (f, d, r)

say(f"""
  The premium per bar is {gross*100:.6f}% and one round trip costs about
  {np.mean(list(SPREAD.values()))*2*100:.4f}% of the traded fraction. Rebalancing
  more often captures more premium but pays more spread. The table shows
  where that trade-off actually lands on real data.""")

say()
say("="*78)
say("3. CAN MY VOLATILITY FORECAST TIME IT? (the whole point)")
say("="*78)
say("The premium is proportional to variance. If I rebalance ONLY when I")
say("predict high dispersion, I should capture more premium per unit of cost.")
say("Forecast = trailing realised dispersion of the 3 assets (causal).")

def run_timed(thresh_q, lookback=20, cost_on=True):
    wts = np.ones(3)/3; eq = 1.0; turn_total = 0.0; nreb = 0
    disp_hist = []
    for t in range(T):
        r = M[:, t]
        eq *= (1 + float(wts @ r))
        wts = wts*(1+r); wts = wts/wts.sum()
        # causal dispersion forecast from the PAST only
        if t >= lookback:
            recent = M[:, t-lookback:t]
            disp = float(np.mean(recent.std(axis=1)))
            disp_hist.append(disp)
            if len(disp_hist) > 30:
                thr = float(np.quantile(disp_hist[:-1], thresh_q))
                if disp >= thr:
                    tgt = np.ones(3)/3
                    turn = float(np.abs(wts-tgt).sum())/2
                    c = turn*float(np.mean(list(SPREAD.values())))*2 if cost_on else 0.0
                    eq *= (1-c); turn_total += turn; nreb += 1
                    wts = tgt
    return eq, turn_total, nreb

say(f"{'rule':30s} {'final eq':>10s} {'vs B&H':>9s} {'#rebal':>8s} {'turnover':>9s}")
for q, lab in [(0.0, 'rebalance every bar'),
               (0.5, 'only top 50% dispersion'),
               (0.7, 'only top 30% dispersion'),
               (0.9, 'only top 10% dispersion')]:
    e, tt, nr = run_timed(q)
    say(f"{lab:30s} {e:10.5f} {e-bh['eq']:+9.5f} {nr:8d} {tt:9.2f}")

say()
say("="*78)
say("4. DECOMPOSITION -- where did every basis point come from?")
say("="*78)
say("The lesson from the last false positive: never trust a total, always")
say("decompose. Rebalanced return = sum of (weights . returns) each bar,")
say("minus costs. No branch of this code can invent PnL: every bar's")
say("contribution is w'r with w summing to 1, so it is a real portfolio.")
f_best = best[0]
r = run(f_best)
say(f"  best fixed frequency: every {f_best} bars")
say(f"  gross growth (before cost) : {(run(f_best, cost_on=False)['eq']-1)*100:+.4f}%")
say(f"  costs paid                 : {-r['cost']*100:+.4f}%")
say(f"  net                        : {(r['eq']-1)*100:+.4f}%")
say(f"  buy & hold                 : {(bh['eq']-1)*100:+.4f}%")
say(f"  REBALANCING ALPHA          : {(r['eq']-bh['eq'])*100:+.4f}%")
say(f"  over {T} bars = {T/130:.1f} months  -> "
    f"{(r['eq']-bh['eq'])/(T/130)*100:+.4f}% per month")

say()
say("="*78)
say("5. IS THE ALPHA STATISTICALLY REAL? bar-by-bar difference")
say("="*78)
rb = run(f_best)['curve']; bhc = bh['curve']
d_rb = np.diff(np.log(rb)); d_bh = np.diff(np.log(bhc))
diff = d_rb - d_bh
m, t, n = tstat(list(diff))
say(f"  per-bar log-return difference: mean {m*100:+.6f}%  t={t:+.2f}  n={n}")
say(f"  sign-flip p = {signflip_null(list(diff)):.4f}")
h = len(diff)//2
m1, t1, _ = tstat(list(diff[:h])); m2, t2, _ = tstat(list(diff[h:]))
say(f"  first half t={t1:+.2f}   second half t={t2:+.2f}")

say()
say("="*78)
say("6. THE SCALING LAW -- what would N uncorrelated assets give?")
say("="*78)
say("premium = 0.5 * sigma^2 * (1 - 1/N) * (1 - rho_avg)  approximately")
rho = float((C.sum()-3)/6)
s2 = float(np.mean(sd**2))
say(f"  measured: sigma^2 = {s2:.3e}  avg rho = {rho:+.3f}")
for N in (3, 5, 10, 20, 50, 100):
    prem = 0.5*s2*(1-1/N)*(1-rho)
    say(f"    N={N:4d}  premium/bar {prem*100:.6f}%  "
        f"per month {prem*130*100:+7.4f}%  per year {prem*1560*100:+8.2f}%")
say("""
  This is the honest ceiling of the no-prediction path, and it scales with
  the number of UNCORRELATED assets -- the one lever that does not require
  forecasting direction.""")
