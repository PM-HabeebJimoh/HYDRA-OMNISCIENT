#!/usr/bin/env python3
"""THE TWO ANGLES I HAVE NEVER TESTED.

A) TERM STRUCTURE as a state variable. VIX3M/VIX and GVZ/VIX are RATIOS - they
   encode fear ACCELERATION, not level. Never used a ratio of two markets.

B) CONDITIONAL DIRECTION. I always tested direction UNCONDITIONALLY.
   Maybe direction is predictable only in SPECIFIC macro states.
   That is the "hidden logic" - not a new signal, a new CONDITION.
"""
import sys, json, glob, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h
A=('gold','eur','aud'); utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h()
D=collections.defaultdict(dict)
for t in sorted(p1):
    d=utc(t).strftime('%Y-%m-%d')
    for a in A:
        b=p1[t][a]
        if a not in D[d]: D[d][a]=dict(b)
        else:
            x=D[d][a]; x['high']=max(x['high'],b['high']); x['low']=min(x['low'],b['low']); x['close']=b['close']
D={d:v for d,v in D.items() if len(v)==3}
M={}
for f in glob.glob('data/raw/macro/*.json'):
    j=json.load(open(f)); M[j['name']]=dict(zip(j['dates'],j['v']))
daily=['VIX','DXY','HYSPREAD','CURVE','GVZ','VIX3M']
days=sorted(set(D)&set.intersection(*[set(M[k]) for k in daily]))
print("="*98); print("A) TERM-STRUCTURE RATIOS — two markets divided, never tested"); print("="*98)
print(f"  {len(days)} common days\n")
rows=[]
for i in range(1,len(days)):
    d0,d1=days[i-1],days[i]
    b=D[d1]
    fwd=np.mean([(b[a]['close']-b[a]['open'])/b[a]['open'] for a in A])
    rng=np.mean([(b[a]['high']-b[a]['low'])/b[a]['open'] for a in A])
    rows.append(dict(
      ts_eq=M['VIX3M'][d0]/M['VIX'][d0],          # equity term structure
      gv_vx=M['GVZ'][d0]/M['VIX'][d0],            # gold fear vs equity fear
      hy_vx=M['HYSPREAD'][d0]/M['VIX'][d0]*100,   # credit vs equity fear
      fwd=fwd,rng=rng,d=d1))
def ic(x,y):
    x=np.array(x);y=np.array(y)
    if x.std()==0: return 0,0
    c=np.corrcoef(x,y)[0,1]; n=len(x)
    return c, c*math.sqrt(n-2)/math.sqrt(max(1-c**2,1e-12))
print(f"  {'ratio':<28} {'IC dir':>9} {'t':>7} {'IC range':>10} {'t':>7}")
for k,lab in (('ts_eq','VIX3M/VIX equity term'),('gv_vx','GVZ/VIX gold-vs-equity fear'),
              ('hy_vx','HY/VIX credit-vs-equity')):
    x=[r[k] for r in rows]
    c1,t1=ic(x,[r['fwd'] for r in rows]); c2,t2=ic(x,[r['rng'] for r in rows])
    f1='*' if abs(t1)>2 else ' '; f2='*' if abs(t2)>2 else ' '
    print(f"  {lab:<28} {c1:+9.4f}{f1}{t1:+7.2f} {c2:+9.4f}{f2}{t2:+7.2f}")
print()
print("="*98); print("B) CONDITIONAL DIRECTION — is direction predictable in SPECIFIC states?"); print("="*98)
print("  Momentum accuracy, split by macro regime (state known at prior close):\n")
mom=[]
for i in range(2,len(days)):
    d0,d1,d2=days[i-2],days[i-1],days[i]
    pb,b=D[d1],D[d2]
    prev=np.mean([(pb[a]['close']-pb[a]['open'])/pb[a]['open'] for a in A])
    fwd=np.mean([(b[a]['close']-b[a]['open'])/b[a]['open'] for a in A])
    mom.append(dict(prev=prev,fwd=fwd,VIX=M['VIX'][d1],ts=M['VIX3M'][d1]/M['VIX'][d1],
                    HY=M['HYSPREAD'][d1],DXY=M['DXY'][d1],GVZ=M['GVZ'][d1],
                    dVIX=M['VIX'][d1]-M['VIX'][d0]))
def acc(sub,flip=1):
    if len(sub)<20: return None
    h=sum(1 for r in sub if np.sign(r['prev'])*flip*np.sign(r['fwd'])>0)
    p=np.array([np.sign(r['prev'])*flip*r['fwd'] for r in sub])
    return h/len(sub)*100,len(sub),p.mean()/(p.std()/np.sqrt(len(p)))
base=acc(mom)
print(f"  UNCONDITIONAL momentum: {base[0]:.2f}% (n={base[1]}, t={base[2]:+.2f})")
print(f"\n  {'condition':<34} {'n':>5} {'momentum':>10} {'t':>7} {'reversal':>10} {'t':>7}")
qs={k:np.quantile([r[k] for r in mom],[.33,.67]) for k in ('VIX','ts','HY','DXY','GVZ','dVIX')}
for k in ('VIX','ts','HY','DXY','GVZ','dVIX'):
    for lo,hi,tag in ((-1e18,qs[k][0],'LOW'),(qs[k][1],1e18,'HIGH')):
        sub=[r for r in mom if lo<=r[k]<hi]
        a1=acc(sub,1); a2=acc(sub,-1)
        if not a1: continue
        f='  <--' if max(abs(a1[2]),abs(a2[2]))>2.0 else ''
        print(f"  {k+' '+tag:<34} {a1[1]:5d} {a1[0]:9.2f}% {a1[2]:+7.2f} {a2[0]:9.2f}% {a2[2]:+7.2f}{f}")
