#!/usr/bin/env python3
"""
AGBA METTA MODEL - AUDUSD + GBPUSD + USDCAD - JULY 2026 - DAILY / 4H / 1H

Model mechanics per src/engine.py:
  regime from real yield (>0.7 CONTRACTION/SHORT, <-0.1 EXPANSION/LONG, else no trade)
  alignment: ALL 3 must close in the regime direction on the SIGNAL bar
  20% equity per trade, equal weight /3, 500x leverage, 1% hard stop

LIVE timing (correct): signal bar i closes -> ENTER bar i+1 open -> stop from actual
entry checked on bar i+1 high/low -> exit bar i+1 close.
SIGNAL-BAR timing (original engine): entry and exit on the signal bar itself.
"""
import json, glob, datetime, collections
import numpy as np

RISK, LEV, STOP, INITIAL = 0.20, 500, 0.01, 100000.0
U = ('AUDUSD','GBPUSD','USDCAD')
utc = lambda t: datetime.datetime.fromtimestamp(int(t), datetime.timezone.utc)

RY = {}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items():
        if 'real_yield' in row: RY[dt]=row['real_yield']

# ---- 1H panel ----
H1 = collections.defaultdict(dict)
for f in glob.glob('data/raw/intraday/AUDUSD_*.json'):
    j=json.load(open(f))
    for i,t in enumerate(j['t']):
        H1[t]['AUDUSD']={'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}
for f in glob.glob('data/raw/intraday_x/*_1h.json'):
    j=json.load(open(f)); s=j['symbol']
    for i,t in enumerate(j['t']):
        H1[t][s]={'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}
H1={t:v for t,v in H1.items() if all(s in v for s in U)}
print(f"1H bars with all 3 assets: {len(H1)}  "
      f"{utc(min(H1)).strftime('%Y-%m-%d %H:%M')} -> {utc(max(H1)).strftime('%Y-%m-%d %H:%M')}")

def resample(p, secs):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%secs)
        for s in U:
            d=p[t][s]
            if s not in B[b]: B[b][s]=dict(d)
            else:
                x=B[b][s]; x['high']=max(x['high'],d['high'])
                x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
H4=resample(H1,14400)

# ---- DAILY panel from the independently fetched daily OHLC ----
DLY=collections.defaultdict(dict)
for f in glob.glob('data/raw/xpairs_ohlc/*.json'):
    j=json.load(open(f)); s=j['symbol']
    if s not in U: continue
    for i,d in enumerate(j['dates']):
        DLY[d][s]={'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}
for dt,row in json.load(open('data/market_data_spot.json')).items():
    if 'aud' in row:
        b=row['aud']; DLY[dt]['AUDUSD']={'open':b['open'],'high':b['high'],'low':b['low'],'close':b['close']}
DLY={d:v for d,v in DLY.items() if all(s in v for s in U)}
print(f"Daily bars with all 3 assets: {len(DLY)}\n")

def regime_of(y):
    if y is None: return 'NO_YIELD',0
    if y>0.7: return 'CONTRACTION',-1
    if y<-0.1: return 'EXPANSION',1
    return 'STABILITY',0

def run(panel, keyfn, live, month='2026-07'):
    keys=sorted(panel); eq=INITIAL; trades=[]; curve=[INITIAL]
    for i in range(len(keys)-1):
        sk=keys[i]; ek=keys[i+1] if live else keys[i]
        if not keyfn(ek).startswith(month): continue
        reg,direction=regime_of(RY.get(keyfn(sk)[:10]))
        if direction==0: continue
        s=panel[sk]
        if direction==-1 and not all(s[a]['close']<s[a]['open'] for a in U): continue
        if direction== 1 and not all(s[a]['close']>s[a]['open'] for a in U): continue
        pos=eq*RISK/3; bar=0.0
        for a in U:
            b=panel[ek][a]; entry=b['open']
            sp=entry*(1+STOP) if direction==-1 else entry*(1-STOP)
            ex,reason,hit=b['close'],'CLOSE',False
            if direction==-1 and b['high']>=sp: ex,reason,hit=sp,'STOP_LOSS',True
            if direction== 1 and b['low'] <=sp: ex,reason,hit=sp,'STOP_LOSS',True
            pp=(entry-ex)/entry if direction==-1 else (ex-entry)/entry
            usd=pp*pos*LEV; bar+=usd
            trades.append(dict(asset=a,dir='SHORT' if direction==-1 else 'LONG',
                signal=keyfn(sk),entry_bar=keyfn(ek),entry=entry,exit=ex,stop=sp,
                pnl_pct=pp*100,pnl_usd=usd,reason=reason,stop_hit=hit,regime=reg))
        eq+=bar; curve.append(eq)
        if eq<=0: eq=0.0; break
    e=np.array(curve); pk=np.maximum.accumulate(e)
    nb=len(curve)-1
    bw=sum(1 for i in range(1,len(curve)) if curve[i]>curve[i-1])
    aw=sum(1 for t in trades if t['pnl_usd']>0)
    return dict(trades=trades,final=eq,ret=(eq/INITIAL-1)*100,bars=nb,
        bar_wr=bw/nb*100 if nb else 0,asset_trades=len(trades),
        asset_wr=aw/len(trades)*100 if trades else 0,
        stops=sum(1 for t in trades if t['stop_hit']),
        dd=((e-pk)/pk).min()*100,
        days=len(set(t['entry_bar'][:10] for t in trades)))

PAN=[('DAILY',DLY,lambda k:k),
     ('4H',H4,lambda k:utc(k).strftime('%Y-%m-%d %H:%M')),
     ('1H',H1,lambda k:utc(k).strftime('%Y-%m-%d %H:%M'))]

print("="*112)
print("AGBA METTA MODEL - AUDUSD + GBPUSD + USDCAD - JULY 2026")
print("="*112)
print(f"Risk {RISK*100:.0f}% | Leverage {LEV}x | Hard stop {STOP*100:.0f}% | Capital ${INITIAL:,.0f}")
print("1H/4H bounded by AUDUSD feed (ends 2026-07-27). Daily covers full month.")
print()
print(f"{'TF':>6} {'timing':>13} {'signals':>8} {'days':>5} {'bar_WR':>8} {'asset_WR':>9} {'stops':>6} {'return':>16} {'maxDD':>10} {'final equity':>15}")
print("-"*112)
RES={}
for tf,pan,kf in PAN:
    for live,lab in ((False,'SIGNAL-BAR'),(True,'LIVE')):
        r=run(pan,kf,live); RES[(tf,lab)]=r
        print(f"{tf:>6} {lab:>13} {r['bars']:8d} {r['days']:5d} {r['bar_wr']:7.1f}% {r['asset_wr']:8.1f}% "
              f"{r['stops']:6d} {r['ret']:15,.2f}% {r['dd']:9.2f}% {r['final']:14,.0f}")
    print()

print("="*112)
print("LIVE TRADE LOG")
print("="*112)
for tf,_,_ in PAN:
    r=RES[(tf,'LIVE')]
    print(f"\n--- {tf}: {len(r['trades'])} asset trades, {r['stops']} stopped ---")
    for t in r['trades'][:18]:
        print(f"  {t['asset']:<7}{t['dir']:<6} sig {t['signal']:>16} -> {t['entry_bar']:>16} | "
              f"{t['entry']:>9.5f} -> {t['exit']:<9.5f} stop {t['stop']:<9.5f} "
              f"{t['pnl_pct']:+7.3f}% {t['pnl_usd']:>13,.0f} {t['reason']}")
    if len(r['trades'])>18: print(f"  ... {len(r['trades'])-18} more (full log in JSON)")
json.dump({f"{a}|{b}":v for (a,b),v in RES.items()},
          open('backtest_results/live_model/july2026_audgbpcad_all_tf.json','w'),indent=2,default=str)
