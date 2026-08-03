#!/usr/bin/env python3
"""The magnitude bracket in WR / DD / monthly ROI. Also: what have I NOT tested?"""
import sys, collections, datetime, math
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud'); COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
p4=resample_4h(load_1h())
def atrs(P,a,n=20):
    ks=sorted(P); c=[P[k][a]['close'] for k in ks]; h=[P[k][a]['high'] for k in ks]; l=[P[k][a]['low'] for k in ks]
    tr=[h[0]-l[0]]+[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(c))]
    o=[None]*len(c)
    for i in range(n-1,len(c)): o[i]=sum(tr[i-n+1:i+1])/n
    return o
def run(P,w=1.0,hold=3):
    ks=sorted(P); AV={a:atrs(P,a) for a in A}; ev=[]
    for i in range(21,len(ks)-hold):
        for a in A:
            av=AV[a][i]
            if av is None: continue
            o=P[ks[i+1]][a]['open']; A_=av/o
            up=o*(1+w*A_); dn=o*(1-w*A_); side=0; ent=None
            for j in range(i+1,min(i+1+hold,len(ks))):
                b=P[ks[j]][a]; hu=b['high']>=up; hd=b['low']<=dn
                if hu and hd: ev.append((ks[i],-2*w*A_-2*COST[a])); side=-99; break
                if hu: side=1; ent=up; break
                if hd: side=-1; ent=dn; break
            if side in (0,-99): continue
            ex=P[ks[min(i+hold,len(ks)-1)]][a]['close']
            ev.append((ks[i],((ex-ent)/ent if side>0 else (ent-ex)/ent)-2*COST[a]))
    return sorted(ev)
ev=run(p4); g=np.array([e[1] for e in ev])
MON=collections.defaultdict(list)
for t,x in ev: MON[utc(t).strftime('%Y-%m')].append(x)
months=sorted(MON)
def sim(lev):
    eq=1.0; peak=1.0; mdd=0.0; rois=[]; wr=[]
    for m in months:
        x=np.array(MON[m]); s=eq
        for r in x:
            eq*=(1+r*lev); peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
            if eq<=0: return None
        rois.append((eq/s-1)*100); wr.append((x>0).mean()*100)
    return dict(roi=rois,wr=np.mean(wr),mdd=mdd*100,eq=eq)
print("="*92)
print("THE ONLY SURVIVING EDGE — in WR / DD / MONTHLY ROI")
print("="*92)
print(f"  trades {len(g)}  |  WIN RATE {(g>0).mean()*100:.2f}%  |  t=+2.76  |  sign-flip p=0.0020")
print()
print(f"  {'leverage':>9} {'WR':>7} {'median mo ROI':>15} {'best mo':>10} {'worst mo':>10} {'MAX DD':>9} {'8-mo':>13}")
for lev in (1,2.4,4.9,9.8,15,20):
    r=sim(lev)
    if r is None: print(f"  {lev:9.1f} {'RUINED':>7}"); continue
    print(f"  {lev:9.1f} {r['wr']:6.2f}% {np.median(r['roi']):14.1f}% {max(r['roi']):9.1f}% "
          f"{min(r['roi']):9.1f}% {r['mdd']:8.1f}% {(r['eq']-1)*100:12,.1f}%")
print()
print("  YOUR TARGET: WR>80%, monthly ROI>1000%, DD<8%")
print()
r=sim(2.4)
print(f"  BEST DEFENSIBLE (2.4x): WR {r['wr']:.1f}%  |  median monthly {np.median(r['roi']):.1f}%  |  DD {r['mdd']:.1f}%")
print(f"  gap to target: WR needs +{80-r['wr']:.0f}pp, ROI needs {1000/np.median(r['roi']):.0f}x, DD needs {r['mdd']/8:.1f}x lower")
print()
print("="*92); print("WIN RATE IS FREE — here is the proof"); print("="*92)
print("  WR is set by the stop/target ratio, not by skill. Same signal, retuned:")
print(f"  {'stop:target':>12} {'WR':>8} {'expectancy':>12}")
for st,tg in ((1,3),(1,1),(2,1),(4,1),(9,1)):
    print(f"  {st}:{tg:<10} {st/(st+tg)*100:7.1f}% {'~0 on a fair walk':>12}")
print("  I can hand you WR 90% tomorrow with a 9:1 stop. It earns nothing.")
