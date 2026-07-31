"""Hand-check the worst cap event from the RAW Investing.com bars: 2026-03-02 16:00 UTC, 4H."""
import sys,datetime
sys.path.insert(0,'scripts')
from intraday_engine import load_1h,resample_4h
p4=resample_4h(load_1h()); keys=sorted(p4)
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)
target=None
for i,k in enumerate(keys):
    if utc(k).strftime('%Y-%m-%d %H:%M')=='2026-03-02 16:00': target=i;break
sk,ek=keys[target-1],keys[target]
s,e=p4[sk],p4[ek]
print("SIGNAL bar",utc(sk),"(this is what triggers the trade)")
for a in ('gold','eur','aud'):
    b=s[a]; print(f"  {a:5s} open={b['open']:<10.5f} close={b['close']:<10.5f} -> {'DOWN' if b['close']<b['open'] else 'UP'} {(b['close']-b['open'])/b['open']*100:+.3f}%")
print("all 3 DOWN -> SHORT, enter next bar open\n")
print("TRADE bar",utc(ek))
eq=875580.0; risk=0.20
# reproduce V3 weights/leverage for this bar
from agba_metta_v3 import atr_pct,grade,W_HIGH,W_NORM,W_LOW,ATR_HIGH,ATR_LOW,WICK_DANGER
xa=atr_pct(keys,p4,target-1,'gold')
w=dict(W_HIGH) if (xa is None or xa>=ATR_HIGH) else (dict(W_LOW) if xa<=ATR_LOW else dict(W_NORM))
g=s['gold']; wick=(g['high']-max(g['open'],g['close']))/g['open']
if wick>WICK_DANGER:
    fr=w['gold']*0.5; w['gold']-=fr; w['eur']+=fr/2; w['aud']+=fr/2
strength=sum(abs(s[a]['close']-s[a]['open'])/s[a]['open'] for a in ('gold','eur','aud'))/3
gr,lev=grade(strength,xa,False,'capped')
print(f"V3 grade={gr} leverage={lev}x  weights={ {k:round(v,3) for k,v in w.items()} }\n")
tot=0
for a in ('gold','eur','aud'):
    b=e[a]; en=b['open']; st=en*1.01
    hit=b['high']>=st; ex=st if hit else b['close']; r=(en-ex)/en
    notion=eq*risk*w[a]*lev
    pnl=r*notion; tot+=pnl
    print(f"  {a:5s} entry={en:<10.5f} high={b['high']:<10.5f} stop={st:<10.5f} {'STOPPED' if hit else 'closed'} exit={ex:<10.5f} move={r*100:+7.3f}%  notional=${notion:,.0f}  P&L=${pnl:,.0f}")
print(f"\n  REAL total P&L = ${tot:,.0f} = {tot/eq*100:.2f}% of ${eq:,.0f} equity")
print(f"  V3 books       = ${-0.02*eq:,.0f} = -2.00%")
print(f"  DIFFERENCE the market charged but the backtest ignored = ${tot+0.02*eq:,.0f}")
