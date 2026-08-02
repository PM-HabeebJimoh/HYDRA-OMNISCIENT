"""
THE LONG-HISTORY TEST -- resolving the n=11 problem.

Previous result: "real yield below 52w median -> gold falls over 26 weeks",
t=-7.13 raw, but only 11 independent windows, and the whole effect came from
2022-2025. Undecidable on that sample.

Now: 23.5 years of MONTHLY data, 2003-01 to 2026-06.
  gold  = FRED IQ12260 (gold price index), 282 months
  ry    = FRED DFII10  (10y TIPS real yield), 282 months
Both real, both official.

This window contains the regimes the 7.6-year sample lacked:
  2003-2007 rising real yields, gold up          (contradicts theory)
  2008-2012 collapsing real yields, gold up      (supports theory)
  2013-2015 taper, real yields up, gold DOWN 45% (supports theory)
  2016-2021 low real yields, gold up             (supports theory)
  2022-2025 real yields to 15y highs, gold up    (contradicts theory)

If the textbook relationship is real, it should show up here. If the
2022-25 inversion was noise, the long sample will say so.

Horizons 1,3,6,12 months. ~23 independent 12m windows, 47 independent 6m.
"""
import json, sys, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'research'))
from calendar_edge import tstat, signflip_null

def say(*a): print(*a, flush=True)

D = json.load(open(ROOT / 'data/raw/long/monthly.json'))
gold = D['gold']
ry = dict(D['ry_pre2019'])
post = """2019-01,0.92 2019-02,0.80 2019-03,0.66 2019-04,0.60 2019-05,0.57 2019-06,0.37 2019-07,0.31 2019-08,0.04 2019-09,0.11 2019-10,0.15 2019-11,0.17 2019-12,0.14 2020-01,0.04 2020-02,-0.11 2020-03,-0.12 2020-04,-0.45 2020-05,-0.44 2020-06,-0.54 2020-07,-0.83 2020-08,-1.01 2020-09,-0.98 2020-10,-0.92 2020-11,-0.84 2020-12,-0.98 2021-01,-1.00 2021-02,-0.92 2021-03,-0.66 2021-04,-0.71 2021-05,-0.85 2021-06,-0.82 2021-07,-1.01 2021-08,-1.07 2021-09,-0.97 2021-10,-0.95 2021-11,-1.06 2021-12,-0.99 2022-01,-0.69 2022-02,-0.52 2022-03,-0.72 2022-04,-0.14 2022-05,0.21 2022-06,0.53 2022-07,0.53 2022-08,0.39 2022-09,1.14 2022-10,1.59 2022-11,1.52 2022-12,1.36 2023-01,1.29 2023-02,1.41 2023-03,1.36 2023-04,1.19 2023-05,1.36 2023-06,1.55 2023-07,1.60 2023-08,1.83 2023-09,2.04 2023-10,2.41 2023-11,2.20 2023-12,1.84 2024-01,1.79 2024-02,1.93 2024-03,1.90 2024-04,2.15 2024-05,2.15 2024-06,2.05 2024-07,1.97 2024-08,1.76 2024-09,1.62 2024-10,1.81 2024-11,2.03 2024-12,2.09 2025-01,2.23 2025-02,2.03 2025-03,1.95 2025-04,2.04 2025-05,2.11 2025-06,2.09 2025-07,2.01 2025-08,1.88 2025-09,1.75 2025-10,1.76 2025-11,1.83 2025-12,1.90 2026-01,1.91 2026-02,1.82 2026-03,1.91 2026-04,1.94 2026-05,2.04 2026-06,2.18"""
for kv in post.split():
    k, v = kv.split(','); ry[k] = float(v)

months = sorted(set(gold) & set(ry))
G = [gold[m] for m in months]
R = [ry[m] for m in months]
say(f"months: {len(months)}  {months[0]} .. {months[-1]}")
say(f"gold index {G[0]:.1f} -> {G[-1]:.1f}  ({G[-1]/G[0]:.2f}x over "
    f"{len(months)/12:.1f} years)")

def fwd(i, h):
    return None if i+h >= len(G) else (G[i+h]-G[i])/G[i]

HOR = (1, 3, 6, 12)

say()
say("="*78)
say("A. THE TEXTBOOK RELATIONSHIP, 23.5 YEARS")
say("="*78)
say("Signal: real yield BELOW its trailing 36m median -> LONG gold.")
say("Expanding median, no look-ahead. Non-overlapping samples only.")
say(f"{'h(mo)':>5s} {'n_ind':>6s} {'acc%':>7s} {'sig%':>8s} {'long-only%':>11s} "
    f"{'excess%':>9s} {'t(exc)':>7s} {'p':>8s}")
for h in HOR:
    sig, raw, acc, hist = [], [], [], []
    for i, m in enumerate(months):
        if len(hist) >= 36:
            s = 1 if R[i] < float(np.median(hist)) else -1
            f = fwd(i, h)
            if f is not None:
                sig.append(s*f); raw.append(f); acc.append(int(np.sign(f) == s))
        hist.append(R[i])
    s_n = sig[::h]; r_n = raw[::h]; a_n = acc[::h]
    exc = [a-b for a, b in zip(s_n, r_n)]
    m1, _, _ = tstat(s_n); m2, _, _ = tstat(r_n)
    me, te, ne = tstat(exc)
    say(f"{h:5d} {ne:6d} {np.mean(a_n)*100:7.2f} {m1*100:+8.3f} "
        f"{m2*100:+11.3f} {me*100:+9.3f} {te:+7.2f} {signflip_null(exc):8.4f}")

say()
say("="*78)
say("B. THE TWO LEGS -- the test that killed the 7.6-year version")
say("="*78)
say("If BOTH legs are positive, it is beta timing, not direction.")
say(f"{'h(mo)':>5s} {'LOW ry leg':>22s} {'HIGH ry leg':>22s}  verdict")
for h in HOR:
    lo, sh, hist = [], [], []
    for i, m in enumerate(months):
        if len(hist) >= 36:
            f = fwd(i, h)
            if f is not None:
                (lo if R[i] < float(np.median(hist)) else sh).append(f)
        hist.append(R[i])
    lo_n, sh_n = lo[::h], sh[::h]
    ml, tl, nl = tstat(lo_n); ms, ts_, ns = tstat(sh_n)
    v = "BOTH POSITIVE -> beta timing" if (ml > 0 and ms > 0) else \
        ("OPPOSITE SIGNS -> real direction" if ml*ms < 0 else "both negative")
    say(f"{h:5d} {ml*100:+8.2f}% (n={nl:3d}) t={tl:+5.2f} "
        f"{ms*100:+8.2f}% (n={ns:3d}) t={ts_:+5.2f}  {v}")

say()
say("="*78)
say("C. REGIME BY REGIME -- is the 2022-25 inversion unique?")
say("="*78)
say("12-month forward gold return, by real-yield direction, per era.")
eras = [('2003-2007', '2003-01', '2007-12'), ('2008-2012', '2008-01', '2012-12'),
        ('2013-2015', '2013-01', '2015-12'), ('2016-2021', '2016-01', '2021-12'),
        ('2022-2026', '2022-01', '2026-06')]
say(f"{'era':11s} {'ry change':>10s} {'gold 1y avg':>12s} {'sign match?':>12s}")
for lab, a, b in eras:
    idx = [i for i, m in enumerate(months) if a <= m <= b]
    if len(idx) < 13: continue
    dry = R[idx[-1]] - R[idx[0]]
    g12 = [fwd(i, 12) for i in idx if fwd(i, 12) is not None]
    gm = np.mean(g12)*100
    # textbook: ry up -> gold down
    match = "YES" if (dry > 0) != (gm > 0) else "NO"
    say(f"{lab:11s} {dry:+10.2f} {gm:+12.2f} {match:>12s}")

say()
say("="*78)
say("D. CONTINUOUS TEST -- correlation of d(real yield) with gold returns")
say("="*78)
say("Not a regime split: the direct relationship, by era and overall.")
for lab, a, b in [('FULL 2003-2026', '2003-01', '2026-06')] + eras:
    idx = [i for i, m in enumerate(months) if a <= m <= b and i+1 < len(G)]
    if len(idx) < 24: continue
    dr = np.array([R[i+1]-R[i] for i in idx])
    gr = np.array([(G[i+1]-G[i])/G[i] for i in idx])
    c = np.corrcoef(dr, gr)[0, 1]
    n = len(dr); t = c*np.sqrt(n-2)/np.sqrt(1-c**2)
    say(f"  {lab:15s} corr(d_ry, gold_ret) = {c:+.4f}  t={t:+6.2f}  n={n}")
say()
say("Textbook says this correlation should be NEGATIVE and stable.")

say()
say("="*78)
say("E. CAN IT PREDICT? contemporaneous vs LAGGED")
say("="*78)
say("Correlation is not prediction. Does LAST month's ry change forecast")
say("NEXT month's gold return?")
for lag in (0, 1, 2, 3):
    idx = [i for i in range(36, len(G)-1-lag)]
    dr = np.array([R[i-lag]-R[i-lag-1] for i in idx])
    gr = np.array([(G[i+1]-G[i])/G[i] for i in idx])
    c = np.corrcoef(dr, gr)[0, 1]
    n = len(dr); t = c*np.sqrt(n-2)/np.sqrt(1-c**2)
    lab = "contemporaneous" if lag == 0 else f"lagged {lag} month(s)"
    say(f"  {lab:20s} corr = {c:+.4f}  t={t:+6.2f}  n={n}")
