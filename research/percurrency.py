"""AGBA-METTA STRUCTURE, per currency, one at a time.
Signal bar closes -> condition checked on that CLOSED bar -> ENTER NEXT BAR OPEN.
No look-ahead anywhere: every signal at bar i uses only bars <= i, trade is bar i+1.
Core 3 (XAU/EUR/AUD) have 409 bars (2025-01 -> 2026-07). Other 7 have 149 (2026)."""
import json,math,datetime
import numpy as np
D=json.load(open('/tmp/allpairs.json'))
SYMS=['XAUUSD','XAGUSD','EURUSD','AUDUSD','GBPUSD','NZDUSD','USDCAD','USDCHF','USDJPY','EURGBP']
CORE=('XAUUSD','EURUSD','AUDUSD')

def series(sym):
    ds=sorted(d for d in D if sym in D[d])
    o=np.array([D[d][sym]['o'] for d in ds]); c=np.array([D[d][sym]['c'] for d in ds])
    return ds,o,c,(c-o)/o

def wilson(k,n):
    if n==0: return (0,0)
    p=k/n; z=1.96; den=1+z*z/n
    ctr=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return ctr-h,ctr+h

def show(k,n,label):
    if n<15: return f"{label:>26}: n={n:<4d} (too few)"
    a=k/n; lo,hi=wilson(k,n)
    sig='*' if lo>0.5 else (' ' if hi>0.5 else 'x')
    return f"{label:>26}: n={n:<4d} acc={a*100:6.2f}%  CI[{lo*100:5.1f},{hi*100:5.1f}] {sig}"

# core-3 alignment computed on the SIGNAL bar (closed), per date
ds_all=sorted(D)
def align_on(dt):
    if not all(s in D[dt] for s in CORE): return None,None
    sg=[np.sign(D[dt][s]['c']-D[dt][s]['o']) for s in CORE]
    st=np.mean([abs(D[dt][s]['c']-D[dt][s]['o'])/D[dt][s]['o'] for s in CORE])
    if abs(sum(sg))!=3: return 0,st
    return int(np.sign(sum(sg))),st

print("="*84)
print("AGBA-METTA TIMING: signal on CLOSED bar i  ->  trade bar i+1 open->close")
print("legend: * = 95% CI excludes 50% (real)   x = significantly WORSE than 50%")
print("="*84)

summary=[]
for sym in SYMS:
    ds,o,c,r=series(sym)
    span=f"{ds[0]} -> {ds[-1]}  ({len(ds)} bars)"
    print(f"\n### {sym}   {span}")
    nxt=np.sign(r[1:])
    # --- A. own prior-bar direction (the single-currency Agba Metta signal)
    for mode,lab in ((1,'own prior bar FOLLOW'),(-1,'own prior bar FADE')):
        s=np.sign(r[:-1])*mode; m=(s!=0)&(nxt!=0)
        print("   "+show(int((s[m]==nxt[m]).sum()),int(m.sum()),lab))
    # --- B. own prior bar with strength gate
    for th in (0.003,0.006):
        s=np.sign(r[:-1]); g=np.abs(r[:-1])>=th; m=g&(s!=0)&(nxt!=0)
        print("   "+show(int((s[m]==nxt[m]).sum()),int(m.sum()),f"own FOLLOW |move|>={th*100:.1f}%"))
        print("   "+show(int((-s[m]==nxt[m]).sum()),int(m.sum()),f"own FADE   |move|>={th*100:.1f}%"))
    # --- C. core-3 Agba Metta alignment on signal bar -> this currency next bar
    al=[];st=[];keep=[]
    for i,dt in enumerate(ds[:-1]):
        a,s_=align_on(dt)
        if a is None: continue
        al.append(a); st.append(s_); keep.append(i)
    al=np.array(al); st=np.array(st); keep=np.array(keep)
    if len(al):
        nx=np.sign(r[1:])[keep]
        f=(al!=0)&(nx!=0)
        for mode,lab in ((1,'AM-align FOLLOW'),(-1,'AM-align FADE')):
            s=al*mode
            print("   "+show(int((s[f]==nx[f]).sum()),int(f.sum()),lab))
        f2=f&(st>=0.003)
        for mode,lab in ((1,'AM-align FOLLOW str>=0.3%'),(-1,'AM-align FADE   str>=0.3%')):
            s=al*mode
            print("   "+show(int((s[f2]==nx[f2]).sum()),int(f2.sum()),lab))
        summary.append((sym,int(f.sum()),(al[f]==nx[f]).mean()))
print("\n"+"="*84)
