#!/usr/bin/env python3
"""AGBA METTA V82 — JULY 2026 ONLY.
Same engine as research/agba_v82.py. Warm-up (MA/ATR/streak) is taken from bars
BEFORE July so no look-ahead and no truncated indicators; only trades ENTERED in
July are counted."""
import sys, bisect, datetime, collections
import numpy as np
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
A=('gold','eur','aud')
p1=load_1h(); p4=resample_4h(p1)
COST={'gold':0.00007,'eur':0.00002,'aud':0.000035}
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
JUL_LO=int(datetime.datetime(2026,7,1,tzinfo=datetime.timezone.utc).timestamp())
JUL_HI=int(datetime.datetime(2026,8,1,tzinfo=datetime.timezone.utc).timestamp())

def series(panel,a):
    ks=sorted(panel)
    return (np.array(ks),np.array([panel[k][a]['open'] for k in ks]),
            np.array([panel[k][a]['high'] for k in ks]),
            np.array([panel[k][a]['low'] for k in ks]),
            np.array([panel[k][a]['close'] for k in ks]))
def feats(o,h,l,c):
    n=len(c); bp=(c>o).astype(float)
    pct=np.zeros(n); pct[1:]=(c[1:]-c[:-1])/c[:-1]
    r3=np.full(n,np.nan); stk=np.full(n,np.nan)
    for i in range(3,n): r3[i]=pct[i-2:i+1].sum()
    for i in range(2,n): stk[i]=bp[i-2:i+1].sum()
    return stk,r3
def atr(h,l,c,p=20):
    n=len(c); tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    a=np.full(n,np.nan)
    for i in range(p-1,n): a[i]=tr[i-p+1:i+1].mean()
    return a

MH=12; MINSTREAK=2
def build(fp,xp,sm,tm,align,trendfilter=False):
    ev=[]; fkeys=sorted(fp)
    for a in A:
        xk,xo,xh,xl,xc=series(xp,a); fk,fo,fh,fl,fc=series(fp,a)
        stk,r3=feats(fo,fh,fl,fc); av=atr(xh,xl,xc,20); fkl=list(fk)
        ma20=np.full(len(fc),np.nan); ma50=np.full(len(fc),np.nan)
        for i in range(19,len(fc)): ma20[i]=fc[i-19:i+1].mean()
        for i in range(49,len(fc)): ma50[i]=fc[i-49:i+1].mean()
        tu=(fc>ma20)&(ma20>ma50); td=(fc<ma20)&(ma20<ma50)
        for i in range(60,len(xc)-MH):
            if not (JUL_LO<=xk[i]<JUL_HI): continue      # JULY ENTRIES ONLY
            j=bisect.bisect_right(fkl,xk[i])-1
            if j<60 or np.isnan(stk[j]) or np.isnan(r3[j]) or np.isnan(av[i]): continue
            up = stk[j]>=MINSTREAK and r3[j]>0
            dn = stk[j]<=(3-MINSTREAK) and r3[j]<0
            if trendfilter: up = up and tu[j]; dn = dn and td[j]
            d='BUY' if up and not dn else ('SELL' if dn and not up else None)
            if d is None: continue
            if align:
                b=fp[fkeys[bisect.bisect_right(fkeys,xk[i])-1]]
                au=all(b[x]['close']>b[x]['open'] for x in A)
                ad=all(b[x]['close']<b[x]['open'] for x in A)
                if not ((d=='BUY' and au) or (d=='SELL' and ad)): continue
            S=xc[i]; stop=S-sm*av[i] if d=='BUY' else S+sm*av[i]
            tgt =S+tm*av[i] if d=='BUY' else S-tm*av[i]
            ex=None; why='time'
            for k in range(i+1,min(i+MH,len(xc))):
                if d=='BUY':
                    if xl[k]<=stop: ex=stop;why='stop';break
                    if xh[k]>=tgt: ex=tgt;why='target';break
                else:
                    if xh[k]>=stop: ex=stop;why='stop';break
                    if xl[k]<=tgt: ex=tgt;why='target';break
            if ex is None: ex=xc[min(i+MH,len(xc)-1)]
            g=(ex-S)/S if d=='BUY' else (S-ex)/S
            ev.append((xk[i],a,d,g-COST[a],abs(S-stop)/S,av[i]/S,why))
    ev.sort(key=lambda e:e[0]); return ev

def equity(ev,risk=0.001,cap0=10000.0):
    cap=cap0; peak=cap; mdd=0.0; Rs=[]
    for e in ev:
        rd=cap*risk; cap+=(e[3]/e[4])*rd
        peak=max(peak,cap); mdd=max(mdd,(peak-cap)/peak); Rs.append(e[3]/e[4])
        if cap<=0: break
    R=np.array(Rs)
    if len(R)==0: return None
    return dict(n=len(R),cap=cap,ret=(cap/cap0-1)*100,mdd=mdd*100,wr=(R>0).mean()*100,
                meanR=R.mean(),t=R.mean()/(R.std()/np.sqrt(len(R))) if R.std()>0 else 0,R=R)

print("="*96)
print("AGBA METTA V82 — JULY 2026")
print("="*96)
print("Universe: XAUUSD/EURUSD/AUDUSD (only assets with verified 1H bars)")
print("Forecast 4H / execute 1H | risk 0.1%/trade | 12-bar time exit | real spreads")
print()
print("COVERAGE: 13 of 23 July weekdays have full 3-asset 1H data.")
print("  ABSENT: 07-03, 07-09, 07-15, 07-21, 07-22, 07-27..07-31")
print("  Binding limit is AUDUSD (14/23 days); EURUSD 16/23; XAUUSD 20/23.")
print("  => July is 57% covered. Results below are for those 13 days only.")
print()
print(f"{'variant':<44} {'n':>5} {'WR':>7} {'meanR':>9} {'t':>7} {'ROI':>10} {'maxDD':>8}")
out={}
for lab,sm,tm,al,tf in (("V82 as-specified (1.0/2.0, trend filter)",1.0,2.0,False,True),
                        ("AGBA V82 (0.5/3.0, no trend filter)",0.5,3.0,False,False),
                        ("AGBA V82 + alignment confluence",0.5,3.0,True,False)):
    ev=build(p4,p1,sm,tm,al,tf); r=equity(ev)
    out[lab]=(ev,r)
    if r is None: print(f"{lab:<44} {'no trades':>40}"); continue
    print(f"{lab:<44} {r['n']:5d} {r['wr']:6.2f}% {r['meanR']:+9.4f} {r['t']:+7.2f} {r['ret']:+9.2f}% {r['mdd']:7.2f}%")

ev,r=out["AGBA V82 + alignment confluence"]
print()
print("="*96); print("AGBA METTA V82 + ALIGNMENT — JULY 2026 DETAIL"); print("="*96)
ex=collections.Counter(e[6] for e in ev)
tot=sum(ex.values())
print(f"  exits: "+"  ".join(f"{k}={v} ({v/tot*100:.1f}%)" for k,v in ex.most_common()))
byd=collections.Counter(utc(e[0]).strftime('%m-%d') for e in ev)
print(f"  trades by day: {dict(sorted(byd.items()))}")
bya=collections.Counter(e[1] for e in ev)
print(f"  trades by asset: {dict(bya)}")
print()
print("  PER-DAY EQUITY PATH (0.1% risk, $10,000 start):")
cap=10000.0; peak=cap
cur=None; dayp=0.0
for e in ev:
    d=utc(e[0]).strftime('%m-%d')
    if cur is None: cur=d
    if d!=cur:
        print(f"    {cur}: P&L {dayp:+9.2f}  equity ${cap:,.2f}")
        cur=d; dayp=0.0
    rd=cap*0.001; g=(e[3]/e[4])*rd; cap+=g; dayp+=g; peak=max(peak,cap)
print(f"    {cur}: P&L {dayp:+9.2f}  equity ${cap:,.2f}")
print()
print("  RISK SCALING (same July signal):")
print(f"    {'risk':>7} {'ROI':>12} {'maxDD':>9}")
for rk in (0.001,0.0025,0.005,0.01):
    rr=equity(ev,risk=rk)
    print(f"    {rk*100:6.2f}% {rr['ret']:11.2f}% {rr['mdd']:8.2f}%")
print()
print("  MOVE-SIZE GATE:")
sz=np.array([e[5] for e in ev]); R=np.array([e[3]/e[4] for e in ev])
q=np.quantile(sz,[0,.5,1.0])
for lo,hi,lab in ((q[0],q[1],'smaller half ATR'),(q[1],q[2],'larger half ATR')):
    m=(sz>=lo)&(sz<=hi); x=R[m]
    print(f"    {lab:<20} n={m.sum():4d} meanR={x.mean():+.4f} t={x.mean()/(x.std()/np.sqrt(len(x))):+6.2f}")
