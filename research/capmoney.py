"""On every bar where V3's -2% cap binds, how big was the REAL loss the market
delivered vs the -2% V3 wrote in the book? A broker pays the real one."""
import sys, collections, datetime
sys.path.insert(0,'scripts')
from agba_metta_v3 import (A, MIN_BASKET_STRENGTH, ATR_HIGH, ATR_LOW, W_HIGH, W_NORM,
                           W_LOW, COOLDOWN_MULT, PROFIT_LOCK_TRIGGER, PROFIT_LOCK_RISK,
                           WICK_DANGER, LADDER, atr_pct, grade)
from intraday_engine import load_1h, resample_4h
p1=load_1h(); p4=resample_4h(p1)
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)

def audit(panel,lo,hi,ladder='capped',base_risk=0.20,eq0=1e5,cap=0.02):
    keys=sorted(panel); eq=eq0; cooldown=False; month_start=eq; ev=[]
    for i in range(len(keys)-1):
        sk,ek=keys[i],keys[i+1]
        if not (lo<=ek<hi): continue
        s,e_=panel[sk],panel[ek]
        dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
        if dn: side=-1
        elif up: side=1
        else: continue
        strength=sum(abs(s[a]['close']-s[a]['open'])/s[a]['open'] for a in A)/3
        if strength<MIN_BASKET_STRENGTH: continue
        xa=atr_pct(keys,panel,i,'gold')
        w=dict(W_HIGH) if (xa is None or xa>=ATR_HIGH) else (dict(W_LOW) if xa<=ATR_LOW else dict(W_NORM))
        g=s['gold']
        wick=((g['high']-max(g['open'],g['close']))/g['open']) if side<0 else ((min(g['open'],g['close'])-g['low'])/g['open'])
        if wick>WICK_DANGER:
            fr=w['gold']*0.5; w['gold']-=fr; w['eur']+=fr/2; w['aud']+=fr/2
        gr,lev=grade(strength,xa,False,ladder)
        if cooldown: lev*=COOLDOWN_MULT
        risk=PROFIT_LOCK_RISK if (eq/month_start-1)>=PROFIT_LOCK_TRIGGER else base_risk
        pnl=0.0; stopped=False
        for a in A:
            b=e_[a]; en=b['open']; notional=eq*risk*w[a]*lev
            if side<0:
                st=en*1.01; hit=b['high']>=st; ex=st if hit else b['close']; r=(en-ex)/en
            else:
                st=en*0.99; hit=b['low']<=st; ex=st if hit else b['close']; r=(ex-en)/en
            if hit: stopped=True
            pnl+=r*notional
        raw=pnl
        if cap is not None and pnl<-cap*eq:
            ev.append((ek,eq,raw,-cap*eq)); pnl=-cap*eq
        eq+=pnl; cooldown=stopped
        if eq<=0: break
    return ev,eq

for nm,pan,tf in (('4H',p4,'4H'),('1H',p1,'1H')):
    ev,eq=audit(pan,1764547200,1782864000)
    print(f"=== {tf} pooled Dec25-Jun26: cap bound {len(ev)} times ===")
    tot=sum(-(r-c) for _,_,r,c in ev)
    print(f"  total loss ABSORBED by the cap (money the book never paid): ${tot:,.0f}")
    worst=sorted(ev,key=lambda x:x[2]/x[1])[:6]
    print(f"  {'bar (UTC)':>17} {'equity':>14} {'REAL move':>11} {'booked':>8}")
    for ts,e,r,c in worst:
        print(f"  {utc(ts).strftime('%Y-%m-%d %H:%M'):>17} {e:14,.0f} {r/e*100:10.2f}% {c/e*100:7.2f}%")
    print()
