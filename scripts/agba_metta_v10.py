"""
AgbaMettaEngine V10 -- the upgraded engine.

What changed from the original:
  ORIGINAL: direction from 3-asset alignment, 20% equity, 500x leverage,
            1% stop, exit next close.  Measured result: blows up.
            (DAILY Feb -95.88%, Mar -100%, Apr -99.64% ...)

  V10:      1. Direction is NOT predictable (40+ tests) -> stop betting on it.
            2. Magnitude IS predictable (IC 0.50, t=+17) -> bet on that.
            3. Trade the bracket (long convexity), not the alignment.
            4. Gate with the economic calendar (known days in advance).
            5. Size at the measured growth optimum k* = mu/sigma^2, not 500x.

This is the best configuration I can defend with real data.
Run:  python3 scripts/agba_metta_v10.py
"""
import json, sys, collections, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events, tstat

SPREAD = {'gold': 0.00012, 'eur': 0.000045, 'aud': 0.000075}

def build():
    p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4)
    EV = build_events()
    sched = collections.Counter(e['ts'] - (e['ts'] % 14400) for e in EV)
    S = {}
    for a in A:
        out, pc = [], None
        for t in b4:
            x = p4[t][a]
            out.append((t, x['open'], x['high'], x['low'], x['close'],
                        pc if pc else x['open']))
            pc = x['close']
        S[a] = out
    return S, b4, sched

def trades(S, b4, sched, hold=3, width=1.0, gate=False):
    """Long-convexity bracket. Worst-case whipsaw. Real spreads."""
    out = []
    for a in A:
        q = S[a]
        for i in range(21, len(q) - hold):
            if gate and sched.get(q[i][0], 0) < 1:
                continue
            atr = np.mean([(q[j][2]-q[j][3])/q[j][1] for j in range(i-20, i)])
            if not atr:
                continue
            o, hs = q[i][1], SPREAD[a]
            w = width * atr
            up, dn = o*(1+w), o*(1-w)
            hu, hd = q[i][2] >= up, q[i][3] <= dn
            if hu and hd:
                r = -2*w - 2*hs                       # whipsawed both ways
            elif hu:
                r = (q[i+hold][4] - up)/o - hs
            elif hd:
                r = (dn - q[i+hold][4])/o - hs
            else:
                continue                              # never triggered
            out.append((q[i][0], a, r))
    return sorted(out)

def equity(T, lev):
    byt = collections.defaultdict(list)
    for t, a, r in T:
        byt[t].append(r)
    eq, peak, dd, curve = 1.0, 1.0, 0.0, {}
    for t in sorted(byt):
        eq *= (1 + lev*float(np.mean(byt[t])))
        peak = max(peak, eq); dd = max(dd, 1 - eq/peak)
        curve[dt.datetime.utcfromtimestamp(t).strftime('%Y-%m')] = eq
        if eq <= 0:
            break
    ks = sorted(curve); mr, prev = [], 1.0
    for k in ks:
        mr.append(curve[k]/prev - 1); prev = curve[k]
    return eq, dd, mr, ks

def main():
    S, b4, sched = build()
    print("=" * 74)
    print("AgbaMettaEngine V10")
    print("=" * 74)

    for lab, gate in [("ALL bars", False), ("CALENDAR-GATED", True)]:
        T = trades(S, b4, sched, gate=gate)
        pnl = [r for _, _, r in T]
        m, t, n = tstat(pnl)
        sd = float(np.std(pnl, ddof=1))
        kstar = m/sd**2 if sd else 0
        print(f"\n{lab}:  n={n}  mean {m*100:+.4f}%  t={t:+.2f}  "
              f"WR {np.mean([x>0 for x in pnl])*100:.1f}%")
        print(f"  per-trade sd {sd*100:.3f}%   growth-optimal k* = {kstar:.2f}")
        print(f"  {'lev':>6s} {'median mo%':>11s} {'worst mo%':>10s} "
              f"{'maxDD%':>8s} {'total%':>10s}")
        for lev in (1.0, 2.0, round(kstar, 1) if kstar > 0 else 3.0, 8.0):
            eq, dd, mr, ks = equity(T, lev)
            if not mr:
                continue
            print(f"  {lev:6.1f} {np.median(mr)*100:+11.2f} "
                  f"{min(mr)*100:+10.2f} {dd*100:8.2f} {(eq-1)*100:+10.2f}")

    # month by month at the growth optimum, all bars
    T = trades(S, b4, sched, gate=False)
    pnl = [r for _, _, r in T]
    m = float(np.mean(pnl)); sd = float(np.std(pnl, ddof=1))
    kstar = m/sd**2
    eq, dd, mr, ks = equity(T, kstar)
    print(f"\nMONTH BY MONTH at growth-optimal leverage {kstar:.2f}x:")
    for k, r in zip(ks, mr):
        flag = "" if r > 0 else "   <-- negative"
        print(f"  {k}  {r*100:+8.2f}%{flag}")
    print(f"\n  months >= +500%: {sum(1 for r in mr if r >= 5.0)} of {len(mr)}")
    print(f"  months positive: {sum(1 for r in mr if r > 0)} of {len(mr)}")

    sr = m/sd*np.sqrt(130)
    print(f"\n  monthly Sharpe {sr:.3f}  ->  "
          f"MAX possible monthly ROI = exp(SR^2/2)-1 = "
          f"{(np.exp(sr**2/2)-1)*100:.2f}%")
    print(f"  For +500%/month you need monthly Sharpe "
          f"{np.sqrt(2*np.log(6)):.3f} (annualised "
          f"{np.sqrt(2*np.log(6))*np.sqrt(12):.2f}).")

if __name__ == '__main__':
    main()
