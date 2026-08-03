"""Full 2026 rerun across Daily / 4H / 1H, original vs reversed, with costs.
Uses the real intraday panels (Investing.com, envelope_fixes=0)."""
import json,sys,collections,datetime
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h

A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)
def daily_from(p):
    B=collections.defaultdict(dict)
    for ts in sorted(p):
        b=ts-(ts%86400)
        for a in A:
            d=p[ts][a]
            if a not in B[b]: B[b][a]=dict(d)
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
pD=daily_from(p1)
LO=datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc).timestamp()
HI=datetime.datetime(2026,8,1,tzinfo=datetime.timezone.utc).timestamp()
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}

def bt(panel,flip,lev,risk=0.20,stop=0.01,eq0=1e5,lo=LO,hi=HI,costs=True):
    keys=sorted(panel); eq=eq0; curve=[]; tr=[]
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s=panel[sk]
        dn=all(s[a]['close']<s[a]['open'] for a in A)
        up=all(s[a]['close']>s[a]['open'] for a in A)
        if not (dn or up): continue
        side=(-1 if dn else 1)*(-1 if flip else 1)
        pnl=0.0; b_=panel[ek]
        for a in A:
            b=b_[a]; e=b['open']; notion=eq*risk/3*lev
            if side<0:
                st=e*(1+stop); hit=b['high']>=st; ex=st if hit else b['close']; r=(e-ex)/e
            else:
                st=e*(1-stop); hit=b['low']<=st; ex=st if hit else b['close']; r=(ex-e)/e
            pnl+=r*notion-(COST[a]*notion if costs else 0)
        eq+=pnl; tr.append(pnl); curve.append(eq)
        if eq<=0: return dict(ret=-100.,dd=-100.,n=len(tr),wr=0.,eq=0.)
    if not tr: return dict(ret=0.,dd=0.,n=0,wr=0.,eq=eq0)
    e=np.array(curve); pk=np.maximum.accumulate(np.concatenate([[eq0],e]))[1:]
    return dict(ret=(eq/eq0-1)*100, dd=((e-pk)/pk).min()*100, n=len(tr),
                wr=sum(1 for x in tr if x>0)/len(tr)*100, eq=eq)

PAN={'DAILY':pD,'4H':p4,'1H':p1}
for lab,flip in (('ORIGINAL (model as-is)',False),('REVERSED (flip side)',True)):
    print("="*92)
    print(f"FULL 2026 - {lab}   [with real spread costs]")
    print("="*92)
    print(f"{'TF':>6} {'lev':>5} {'trades':>7} {'winrate':>8} {'return':>15} {'maxDD':>10} {'final eq':>14}")
    for tf in ('DAILY','4H','1H'):
        for lev in (500,100,25,10,5,2,1):
            r=bt(PAN[tf],flip,lev)
            print(f"{tf:>6} {lev:5d} {r['n']:7d} {r['wr']:7.1f}% {r['ret']:14,.2f}% {r['dd']:9.2f}% {r['eq']:13,.0f}")
        print()

print("="*92)
print("BEST SIZE RESPECTING DD < 5%  (reversed direction, with costs)")
print("="*92)
for tf in ('DAILY','4H','1H'):
    best=None
    for lev in np.arange(0.5,60,0.5):
        r=bt(PAN[tf],True,lev)
        if r['dd']>-5.0: best=(lev,r)
    if best:
        lev,r=best; mo=(1+r['ret']/100)**(1/7.0)-1
        print(f"  {tf:>5}: lev {lev:5.1f}x  trades {r['n']:4d}  WR {r['wr']:.1f}%  "
              f"return {r['ret']:+8.2f}%  DD {r['dd']:6.2f}%  -> {mo*100:+.2f}%/month")
