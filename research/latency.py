"""
THE LATENCY TEST -- the one experiment that can still change the answer.

Established: on 1H bars, trading the surprise gave t=+2.37 on the bar
CONTAINING the release, and t=+0.31 on the first bar you can actually enter.
The entire directional edge lived inside a 30-minute hole I could not see into.

Now I can see into it. 435 real Investing.com 5-minute XAUUSD bars around 14
releases. The question is precise:

    Direction IS predictable at the instant of release. How long does it last?

If the edge survives 5, 10, 15 minutes AFTER the print, it is tradeable and
this project has a directional signal. If it is gone by the first 5-min bar
you can enter, then the edge lives inside <5 minutes and is unreachable
without colocation -- and that is a physical answer, not a modelling failure.

Entry convention: the release lands at T. The 5-min bar [T, T+5) contains it
and is NOT enterable (you would have to be positioned at T, before the number
exists). The first honest entry is the OPEN of the bar starting at T+5.
"""
import json, sys, datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'research'))
from calendar_edge import tstat, signflip_null

M5 = {int(k): v for k, v in
      json.load(open(ROOT / 'data/raw/m5/xauusd_m5.json')).items()}
REL = json.load(open(ROOT / 'data/raw/oos/release_instants.json'))
USD_TO_ASSET = -1          # gold is quoted vs USD

print(f"5-min bars available : {len(M5)}")
print(f"release instants     : {len(REL)}")

def bar(t):
    return M5.get(t - (t % 300))

# keep only releases we actually have bars for, with enough forward coverage
usable = []
for r in REL:
    T = r['epoch'] - (r['epoch'] % 300)
    if all((T + 300 * k) in M5 for k in range(0, 7)):
        usable.append((r, T))
print(f"releases with >=30min of 5-min coverage: {len(usable)}")
print()
for r, T in usable:
    print(f"  {r['ds']} {r['ts']}  z={r['z']:+5.2f}  {','.join(r['names'])}")

print()
print("=" * 76)
print("HOW THE MOVE DECOMPOSES, MINUTE BY MINUTE")
print("=" * 76)
print("Signed by the surprise: positive = price moved the way the")
print("surprise said it should (USD-bullish surprise -> gold down).")
print()
print(f"{'window':28s} {'mean%':>9s} {'t':>7s} {'n':>4s} {'WR%':>6s}  enterable?")

def signed(seg_fn):
    out = []
    for r, T in usable:
        s = np.sign(r['z']) * USD_TO_ASSET
        v = seg_fn(T)
        if v is not None:
            out.append(s * v)
    return out

def ret(a, b):
    """return from open of bar a to close of bar b"""
    def f(T):
        ba, bb = M5.get(T + 300 * a), M5.get(T + 300 * b)
        if not ba or not bb:
            return None
        return (bb[3] - ba[0]) / ba[0]
    return f

rows = [
    ("release bar  T..T+5",      ret(0, 0), "NO  (need position at T)"),
    ("T+5 .. T+10",              ret(1, 1), "YES (first honest entry)"),
    ("T+10 .. T+15",             ret(2, 2), "YES"),
    ("T+15 .. T+20",             ret(3, 3), "YES"),
    ("T+5 .. T+15  (hold 2)",    ret(1, 2), "YES"),
    ("T+5 .. T+20  (hold 3)",    ret(1, 3), "YES"),
    ("T+5 .. T+30  (hold 5)",    ret(1, 5), "YES"),
]
res = {}
for lab, fn, ent in rows:
    v = signed(fn)
    m, t, n = tstat(v)
    res[lab] = v
    wr = np.mean([x > 0 for x in v]) * 100 if v else np.nan
    print(f"{lab:28s} {m*100:+9.4f} {t:+7.2f} {n:4d} {wr:6.1f}  {ent}")

print()
print("=" * 76)
print("WHERE INSIDE THE RELEASE BAR DOES THE MOVE HAPPEN?")
print("=" * 76)
print("The release bar's own high/low tell us the move is essentially")
print("instantaneous: compare the full bar move against what remains.")
inst, after = [], []
for r, T in usable:
    s = np.sign(r['z']) * USD_TO_ASSET
    b0, b1 = M5[T], M5[T + 300]
    inst.append(s * (b0[3] - b0[0]) / b0[0])
    after.append(s * (b1[3] - b1[0]) / b1[0])
mi, ti, _ = tstat(inst)
ma, ta, _ = tstat(after)
print(f"  release 5-min bar  mean {mi*100:+.4f}%  t={ti:+.2f}")
print(f"  next    5-min bar  mean {ma*100:+.4f}%  t={ta:+.2f}")
if abs(mi) > 1e-12:
    print(f"  fraction of the move still available after 5 min: "
          f"{ma/mi*100:+.1f}%")

print()
print("=" * 76)
print("COST REALITY CHECK")
print("=" * 76)
print("Gold spread widens hugely at a print. Even at a calm 12c half-spread,")
print("a round trip costs ~0.006% of a $4,000 price. At release it is far worse.")
for lab in ("T+5 .. T+10", "T+5 .. T+20  (hold 3)"):
    v = res[lab]
    m, t, n = tstat(v)
    for hs in (0.00012, 0.00050, 0.00150):
        net = [x - 2 * hs for x in v]
        mn, tn, _ = tstat(net)
        print(f"  {lab:24s} half-spread {hs*100:.3f}%  ->  "
              f"net {mn*100:+.4f}%  t={tn:+.2f}")

print()
print("=" * 76)
print("VERDICT")
print("=" * 76)
v = res["T+5 .. T+10"]
m, t, n = tstat(v)
p = signflip_null(v) if len(v) >= 3 else float('nan')
print(f"  First enterable 5-min bar: mean {m*100:+.4f}%  t={t:+.2f}  "
      f"n={n}  sign-flip p={p:.4f}")
if abs(t) < 1.96:
    print("  Direction is NOT recoverable at 5-minute granularity either.")
    print("  The edge lives inside the first 5 minutes -- most likely the")
    print("  first seconds. That is a LATENCY wall, not a modelling failure.")
else:
    print("  Direction SURVIVES into the enterable window. This is real.")
