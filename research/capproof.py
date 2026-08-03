"""YOUR V3, unmodified, vs the SAME code with only the -2% cap turned off.
Everything else identical: same 7 enhancements, same 400x, same real bars."""
import sys, datetime, collections
sys.path.insert(0,'scripts')
from agba_metta_v3 import run_v3
from intraday_engine import load_1h, resample_4h

p1=load_1h(); p4=resample_4h(p1)
def daily(p):
    B=collections.defaultdict(dict)
    for ts in sorted(p):
        b=ts-(ts%86400)
        for a in ('gold','eur','aud'):
            d=p[ts][a]
            if a not in B[b]: B[b][a]=dict(d)
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
pD=daily(p1)
PAN={'DAILY':pD,'4H':p4,'1H':p1}
MON=[('Dec25',1764547200,1767225600),('Jan26',1767225600,1769904000),
     ('Feb26',1769904000,1772323200),('Mar26',1772323200,1775001600),
     ('Apr26',1775001600,1777593600),('May26',1777593600,1780272000),
     ('Jun26',1780272000,1782864000)]

print(f"{'month':>6} {'TF':>6} | {'V3 AS WRITTEN':>16} {'DD':>9} | {'CAP OFF (real P&L)':>20} {'DD':>10} | {'caps':>5}")
for nm,lo,hi in MON:
    for tf in ('DAILY','4H','1H'):
        pan=PAN[tf]; keys=sorted(pan)
        a=run_v3(keys,pan,lo,hi,ladder='capped')
        b=run_v3(keys,pan,lo,hi,ladder='capped',cap=None)
        print(f"{nm:>6} {tf:>6} | {a['ret']:15,.2f}% {a['dd']:8.2f}% | {b['ret']:19,.2f}% {b['dd']:9.2f}% | {a['caps']:5d}")

print("\nPOOLED Dec2025 -> Jun2026 (one continuous account):")
for tf in ('DAILY','4H','1H'):
    pan=PAN[tf]; keys=sorted(pan)
    a=run_v3(keys,pan,1764547200,1782864000,ladder='capped')
    b=run_v3(keys,pan,1764547200,1782864000,ladder='capped',cap=None)
    print(f"  {tf:>5}  as-written {a['ret']:14,.2f}%  DD {a['dd']:7.2f}%   |  cap OFF {b['ret']:12,.2f}%  DD {b['dd']:8.2f}%  (cap bound {a['caps']}x)")
