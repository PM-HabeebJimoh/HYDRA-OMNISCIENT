"""Best-effort MULTI-INSTRUMENT portfolio, walk-forward, leak-free, with costs.
Signal: previous-day o->c per instrument (momentum & reversal), risk-parity sized,
optionally dollar-factor-neutralised. Goal: maximise monthly ROI at DD<5%."""
import numpy as np, json, math
R=np.load('/tmp/R.npy'); meta=json.load(open('/tmp/Rmeta.json'))
syms=meta['syms']; dates=meta['dates']; n,m=R.shape
print(f"{n} daily bars x {m} instruments, {dates[0]}..{dates[-1]}")
COST=np.array([0.00007,0.00002,0.000035,0.00003,0.00005,0.00004,0.00004,0.00003,0.00004,0.00025])

def mdd(eq):
    pk=np.maximum.accumulate(eq); return ((eq-pk)/pk).min()*100

def run(mode,lb,vol_lb,neutral,k):
    """mode: +1 momentum, -1 reversal. Sizes by inverse trailing vol. Leak-free."""
    pos=np.zeros((n,m))
    for i in range(max(lb,vol_lb)+1,n):
        past=R[i-lb:i]                 # strictly before bar i
        sig=np.sign(past.mean(0))*mode
        vol=R[i-vol_lb:i].std(0)+1e-9
        w=sig/vol
        if neutral:                    # remove the common dollar factor
            pc=R[:i].mean(0)*0
            f=np.ones(m); f[[5,6,7]]=-1  # USDxxx invert -> all 'USD-down' oriented
            proj=(w*f).sum()/m
            w=w-proj*f
        s=np.abs(w).sum()
        if s>0: pos[i]=w/s*k
    gross=(pos*R).sum(1)
    turn=np.abs(np.diff(np.vstack([np.zeros(m),pos]),axis=0))
    cost=(turn*COST).sum(1)
    net=gross-cost
    eq=np.cumprod(1+net)
    months=n/21.0
    return eq[-1]**(1/months)-1, mdd(eq), net.mean()/(net.std()+1e-12)*math.sqrt(252), eq

best=[]
for mode in (1,-1):
    for lb in (1,2,3,5,10,20):
        for vol_lb in (10,20,60):
            for neutral in (False,True):
                mo,dd,sr,_=run(mode,lb,vol_lb,neutral,1.0)
                best.append((sr,mode,lb,vol_lb,neutral,mo,dd))
best.sort(reverse=True)
print(f"\n{'mode':>6} {'lb':>3} {'vol':>4} {'neut':>5} {'monthly%':>9} {'DD%':>8} {'annSR':>7}")
for sr,mode,lb,vl,nt,mo,dd in best[:10]:
    print(f"{'mom' if mode>0 else 'rev':>6} {lb:3d} {vl:4d} {str(nt):>5} {mo*100:+9.2f} {dd:8.2f} {sr:+7.2f}")

sr,mode,lb,vl,nt,_,_=best[0]
print(f"\nScaling the BEST config (annSR {sr:+.2f}) to the 5% DD budget:")
print(f"{'k':>7} {'monthly%':>10} {'maxDD%':>9}")
ok=None
for k in (0.25,0.5,1,2,3,5,8,12,20):
    mo,dd,_,_=run(mode,lb,vl,nt,k)
    print(f"{k:7.2f} {mo*100:+10.2f} {dd:9.2f}")
for k in np.arange(0.05,30,0.05):
    mo,dd,_,_=run(mode,lb,vl,nt,k)
    if dd>-5.0: ok=(k,mo,dd)
print(f"\nMax size respecting DD<5%: k={ok[0]:.2f} -> monthly {ok[1]*100:+.2f}%  DD {ok[2]:.2f}%" if ok else "\nnone")
print(f"GOAL 700%/mo. Achieved {ok[1]*100:.2f}%/mo -> shortfall {700/max(ok[1]*100,1e-9):,.0f}x" if ok else "")
