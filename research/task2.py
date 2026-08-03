#!/usr/bin/env python3
"""TASK 2 — STOP BETTING DIRECTION. BET MAGNITUDE.

The signal knows: after alignment, next candle range is 1.104x (4H) / 1.109x (1H).
It does NOT know direction (52.61% / 48.75%).

Direction-neutral execution = STRADDLE. With spot only: a BRACKET.
  place buy-stop at open*(1+w*ATR) and sell-stop at open*(1-w*ATR)
  whichever fires, ride it; the other is cancelled
  you profit from SIZE of move, never need to know the side

HONEST HANDLING: if BOTH triggers hit inside one candle, OHLC cannot say which
came first -> book it as the WORST case (whipsawed both ways, full double loss).
Real spreads on both legs.
"""
import sys, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p1=load_1h(); p4=resample_4h(p1)
def daily(p):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%86400)
        for a in A:
            d=p[t][a]
            if a not in B[b]: B[b][a]=dict(d)
            else:
                x=B[b][a]; x['high']=max(x['high'],d['high']); x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
PAN={'DAILY':daily(p1),'4H':p4,'1H':p1}
def atrs(P,a,n=20):
    ks=sorted(P); c=[P[k][a]['close'] for k in ks]; h=[P[k][a]['high'] for k in ks]; l=[P[k][a]['low'] for k in ks]
    tr=[h[0]-l[0]]+[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(c))]
    out=[None]*len(c)
    for i in range(n-1,len(c)): out[i]=sum(tr[i-n+1:i+1])/n
    return out

def run(P,w,hold,gate=True):
    """gate=True -> only after Agba Metta alignment fires (the model's signal)"""
    ks=sorted(P); AV={a:atrs(P,a) for a in A}; ev=[]
    for i in range(21,len(ks)-hold):
        s=P[ks[i]]
        aligned = all(s[a]['close']>s[a]['open'] for a in A) or all(s[a]['close']<s[a]['open'] for a in A)
        if gate and not aligned: continue
        for a in A:
            av=AV[a][i]
            if av is None: continue
            o=P[ks[i+1]][a]['open']; A_=av/o
            up=o*(1+w*A_); dn=o*(1-w*A_); side=0; ent=None
            for j in range(i+1,min(i+1+hold,len(ks))):
                b=P[ks[j]][a]; hu=b['high']>=up; hd=b['low']<=dn
                if hu and hd: ev.append((ks[i],a,-2*w*A_-2*COST[a])); side=-99; break
                if hu: side=1; ent=up; break
                if hd: side=-1; ent=dn; break
            if side in (0,-99): continue
            ex=P[ks[min(i+hold,len(ks)-1)]][a]['close']
            g=(ex-ent)/ent if side>0 else (ent-ex)/ent
            ev.append((ks[i],a,g-2*COST[a]))
    return ev
print("="*100)
print("TASK 2 — MAGNITUDE BET (bracket on the Agba Metta alignment signal)")
print("="*100)
print(f"{'TF':>6} {'width':>6} {'hold':>5} {'n':>5} {'WR':>7} {'mean':>10} {'t':>7}")
best=[]
for tf,P in PAN.items():
    for w in (0.5,0.75,1.0,1.5):
        for hold in (1,2,3):
            ev=run(P,w,hold)
            if len(ev)<60: continue
            g=np.array([e[2] for e in ev])
            t=g.mean()/(g.std()/np.sqrt(len(g)))
            best.append((t,tf,w,hold,g,ev))
            if t>1.5:
                print(f"{tf:>6} {w:6.2f} {hold:5d} {len(g):5d} {(g>0).mean()*100:6.2f}% {g.mean()*100:+9.4f}% {t:+7.2f}")
best.sort(reverse=True)
print(f"\nTOP 5 of {len(best)} configs:")
for t,tf,w,hold,g,ev in best[:5]:
    print(f"  {tf:>5} w={w} hold={hold}: n={len(g)} mean={g.mean()*100:+.4f}% t={t:+.2f}")
# compare gated vs ungated -> does the ALIGNMENT add value?
print(f"\n{'='*100}")
print("DOES THE AGBA METTA SIGNAL ADD VALUE TO THE MAGNITUDE BET?")
print("="*100)
t,tf,w,hold,g,ev=best[0]
P=PAN[tf]
ug=run(P,w,hold,gate=False)
gu=np.array([e[2] for e in ug])
print(f"  {tf} w={w} hold={hold}")
print(f"    WITH alignment gate : n={len(g):5d} mean={g.mean()*100:+.4f}% t={t:+.2f}")
print(f"    WITHOUT gate (all)  : n={len(gu):5d} mean={gu.mean()*100:+.4f}% t={gu.mean()/(gu.std()/np.sqrt(len(gu))):+.2f}")
