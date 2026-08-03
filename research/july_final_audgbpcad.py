#!/usr/bin/env python3
"""AGBA METTA - AUDUSD+GBPUSD+USDCAD - JULY 2026 - Daily/4H/1H
Coverage is ASSERTED against the July weekday calendar and printed, not self-reported."""
import json, glob, datetime, collections
import numpy as np
RISK, LEV, STOP, INITIAL = 0.20, 500, 0.01, 100000.0
U=('AUDUSD','GBPUSD','USDCAD')
utc=lambda t: datetime.datetime.fromtimestamp(int(t),datetime.timezone.utc)

RY={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items():
        if 'real_yield' in row: RY[dt]=row['real_yield']

H1=collections.defaultdict(dict)
for f in glob.glob('data/raw/intraday/AUDUSD_*.json'):
    j=json.load(open(f))
    for i,t in enumerate(j['t']):
        H1[t]['AUDUSD']={'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}
for f in glob.glob('data/raw/intraday_x/*_1h.json'):
    j=json.load(open(f)); s=j['symbol']
    for i,t in enumerate(j['t']):
        H1[t][s]={'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}
H1={t:v for t,v in H1.items() if all(s in v for s in U)}

WD=[]
d=datetime.date(2026,7,1)
while d.month==7:
    if d.weekday()<5: WD.append(d.strftime('%m-%d'))
    d+=datetime.timedelta(days=1)
cnt=collections.Counter(utc(t).strftime('%m-%d') for t in H1 if utc(t).strftime('%Y-%m')=='2026-07')
full=[k for k in sorted(cnt) if cnt[k]>=20]
print("="*104)
print("COVERAGE AUDIT (asserted, not self-reported)")
print("="*104)
print(f"  July 2026 weekdays                    : {len(WD)}")
print(f"  Days with >=20 aligned 3-asset 1H bars: {len(full)}")
print(f"  Present : {full}")
print(f"  ABSENT  : {[d for d in WD if d not in full]}")
print(f"  1H COVERAGE = {len(full)}/{len(WD)} = {len(full)/len(WD)*100:.0f}%   <-- NOT a full month")
print()

def resample(p,secs):
    B=collections.defaultdict(dict)
    for t in sorted(p):
        b=t-(t%secs)
        for s in U:
            dd=p[t][s]
            if s not in B[b]: B[b][s]=dict(dd)
            else:
                x=B[b][s]; x['high']=max(x['high'],dd['high']); x['low']=min(x['low'],dd['low']); x['close']=dd['close']
    return {t:v for t,v in B.items() if len(v)==3}
H4=resample(H1,14400)

DLY=collections.defaultdict(dict)
for f in glob.glob('data/raw/xpairs_ohlc/*.json'):
    j=json.load(open(f)); s=j['symbol']
    if s not in U: continue
    for i,dt in enumerate(j['dates']):
        DLY[dt][s]={'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}
for dt,row in json.load(open('data/market_data_spot.json')).items():
    if 'aud' in row:
        b=row['aud']; DLY[dt]['AUDUSD']={'open':b['open'],'high':b['high'],'low':b['low'],'close':b['close']}
DLY={d:v for d,v in DLY.items() if all(s in v for s in U)}
dj=[d for d in DLY if d.startswith('2026-07')]
print(f"  DAILY coverage = {len(dj)}/{len(WD)} weekdays = {len(dj)/len(WD)*100:.0f}%")
print()

def regime_of(y):
    if y is None: return 'NO_YIELD',0
    if y>0.7: return 'CONTRACTION',-1
    if y<-0.1: return 'EXPANSION',1
    return 'STABILITY',0

def run(panel,kf,live):
    keys=sorted(panel); eq=INITIAL; tr=[]; curve=[INITIAL]
    for i in range(len(keys)-1):
        sk=keys[i]; ek=keys[i+1] if live else keys[i]
        if not kf(ek).startswith('2026-07'): continue
        reg,dr=regime_of(RY.get(kf(sk)[:10]))
        if dr==0: continue
        s=panel[sk]
        if dr==-1 and not all(s[a]['close']<s[a]['open'] for a in U): continue
        if dr== 1 and not all(s[a]['close']>s[a]['open'] for a in U): continue
        pos=eq*RISK/3; bar=0.0
        for a in U:
            b=panel[ek][a]; en=b['open']
            sp=en*(1+STOP) if dr==-1 else en*(1-STOP)
            ex,rs,hit=b['close'],'CLOSE',False
            if dr==-1 and b['high']>=sp: ex,rs,hit=sp,'STOP_LOSS',True
            if dr== 1 and b['low'] <=sp: ex,rs,hit=sp,'STOP_LOSS',True
            pp=(en-ex)/en if dr==-1 else (ex-en)/en
            usd=pp*pos*LEV; bar+=usd
            tr.append(dict(asset=a,dir='SHORT' if dr==-1 else 'LONG',sig=kf(sk),ent=kf(ek),
                entry=en,exit=ex,stop=sp,pnl_pct=pp*100,pnl_usd=usd,reason=rs,hit=hit))
        eq+=bar; curve.append(eq)
        if eq<=0: eq=0.0; break
    e=np.array(curve); pk=np.maximum.accumulate(e); nb=len(curve)-1
    bw=sum(1 for i in range(1,len(curve)) if curve[i]>curve[i-1])
    aw=sum(1 for t in tr if t['pnl_usd']>0)
    return dict(trades=tr,final=eq,ret=(eq/INITIAL-1)*100,bars=nb,
        bar_wr=bw/nb*100 if nb else 0,asset_wr=aw/len(tr)*100 if tr else 0,
        stops=sum(1 for t in tr if t['hit']),dd=((e-pk)/pk).min()*100,
        days=len(set(t['ent'][:10] for t in tr)))

PAN=[('DAILY',DLY,lambda k:k),('4H',H4,lambda k:utc(k).strftime('%Y-%m-%d %H:%M')),
     ('1H',H1,lambda k:utc(k).strftime('%Y-%m-%d %H:%M'))]
print("="*104)
print("AGBA METTA MODEL - AUDUSD+GBPUSD+USDCAD - JULY 2026")
print("="*104)
print(f"Risk {RISK*100:.0f}% | Leverage {LEV}x | Hard stop {STOP*100:.0f}% | Capital ${INITIAL:,.0f}")
print()
print(f"{'TF':>6} {'timing':>13} {'signals':>8} {'days':>5} {'bar_WR':>8} {'asset_WR':>9} {'stops':>6} {'return':>15} {'maxDD':>10} {'final':>14}")
print("-"*104)
RES={}
for tf,pan,kf in PAN:
    for live,lab in ((False,'SIGNAL-BAR'),(True,'LIVE')):
        r=run(pan,kf,live); RES[(tf,lab)]=r
        print(f"{tf:>6} {lab:>13} {r['bars']:8d} {r['days']:5d} {r['bar_wr']:7.1f}% {r['asset_wr']:8.1f}% "
              f"{r['stops']:6d} {r['ret']:14,.2f}% {r['dd']:9.2f}% {r['final']:13,.0f}")
    print()
print("="*104); print("LIVE TRADE LOG"); print("="*104)
for tf,_,_ in PAN:
    r=RES[(tf,'LIVE')]
    print(f"\n--- {tf}: {len(r['trades'])} asset trades, {r['stops']} stopped ---")
    for t in r['trades'][:15]:
        print(f"  {t['asset']:<7}{t['dir']:<6} {t['sig']:>16} -> {t['ent']:>16} | {t['entry']:>9.5f} -> {t['exit']:<9.5f} "
              f"{t['pnl_pct']:+7.3f}% {t['pnl_usd']:>12,.0f} {t['reason']}")
    if len(r['trades'])>15: print(f"  ... {len(r['trades'])-15} more")
json.dump({f"{a}|{b}":v for (a,b),v in RES.items()},
    open('backtest_results/live_model/july2026_audgbpcad_final.json','w'),indent=2,default=str)
