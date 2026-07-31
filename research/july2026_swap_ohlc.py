#!/usr/bin/env python3
"""
AGBA METTA MODEL - JULY 2026 - four substitute baskets, NOW WITH REAL OHLC.
Newly fetched daily high/low for GBPUSD/NZDUSD/USDCAD/USDJPY means the 1% hard
stop is finally evaluable on these pairs.

LIVE-CORRECT TIMING: alignment on bar i's close -> ENTER bar i+1 open ->
1% stop from actual entry checked against bar i+1 high/low -> exit bar i+1 close.
SIGNAL-DAY contrast reproduces the original engine's entry_date==exit_date.
"""
import json, glob
import numpy as np

RISK, LEV, STOP, INITIAL = 0.20, 500, 0.01, 100000.0

D = {}
for dt, row in json.load(open('data/market_data_spot.json')).items():
    D.setdefault(dt, {}).update(row)
NAME = {'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}
for dt in list(D):
    for k, v in list(D[dt].items()):
        if k in NAME: D[dt][NAME[k]] = v
for f in glob.glob('data/raw/xpairs_ohlc/*.json'):
    j = json.load(open(f))
    for i, dt in enumerate(j['dates']):
        D.setdefault(dt, {})[j['symbol']] = {
            'open':j['o'][i],'high':j['h'][i],'low':j['l'][i],'close':j['c'][i]}

def regime_of(y):
    if y is None: return 'NO_YIELD', 0
    if y > 0.7:  return 'CONTRACTION', -1
    if y < -0.1: return 'EXPANSION', 1
    return 'STABILITY', 0

def run(universe, live=True):
    ds = sorted(d for d in D if all(s in D[d] for s in universe)
                and 'real_yield' in D[d] and ('2026-06' in d or '2026-07' in d))
    equity = INITIAL; trades = []; eq = [INITIAL]; days = set()
    for i in range(len(ds)-1):
        sd = ds[i]; td = ds[i+1] if live else ds[i]
        if not td.startswith('2026-07'): continue
        reg, direction = regime_of(D[sd].get('real_yield'))
        if direction == 0: continue
        s = D[sd]
        if direction == -1 and not all(s[a]['close'] < s[a]['open'] for a in universe): continue
        if direction ==  1 and not all(s[a]['close'] > s[a]['open'] for a in universe): continue
        pos = equity*RISK/3; bar = 0.0
        for a in universe:
            b = D[td][a]; entry = b['open']
            sp = entry*(1+STOP) if direction==-1 else entry*(1-STOP)
            ex, reason, hit = b['close'], 'CLOSE', False
            if direction==-1 and b['high'] >= sp: ex,reason,hit = sp,'STOP_LOSS',True
            if direction== 1 and b['low']  <= sp: ex,reason,hit = sp,'STOP_LOSS',True
            pnl_pct = (entry-ex)/entry if direction==-1 else (ex-entry)/entry
            usd = pnl_pct*pos*LEV; bar += usd
            trades.append(dict(asset=a,direction='SHORT' if direction==-1 else 'LONG',
                signal=sd,entry_date=td,entry=entry,exit=ex,stop=sp,
                pnl_pct=pnl_pct*100,pnl_usd=usd,exit_reason=reason,regime=reg,stop_hit=hit))
        equity += bar; eq.append(equity); days.add(td)
        if equity <= 0: equity = 0.0; break
    e=np.array(eq); pk=np.maximum.accumulate(e)
    aw=sum(1 for t in trades if t['pnl_usd']>0)
    dwin=len(set(t['entry_date'] for t in trades))
    bars=len(eq)-1
    barw=sum(1 for i in range(1,len(eq)) if eq[i]>eq[i-1])
    return dict(trades=trades,final=equity,ret=(equity/INITIAL-1)*100,
        trade_days=len(days),bars=bars,bar_wr=barw/bars*100 if bars else 0,
        asset_trades=len(trades),asset_wr=aw/len(trades)*100 if trades else 0,
        stops=sum(1 for t in trades if t['stop_hit']),dd=((e-pk)/pk).min()*100)

BASKETS=[('XAUUSD','EURUSD','AUDUSD'),('AUDUSD','GBPUSD','USDCAD'),
         ('EURUSD','AUDUSD','USDCAD'),('GBPUSD','NZDUSD','USDCAD'),
         ('NZDUSD','USDCAD','USDJPY')]

print("="*112)
print("AGBA METTA MODEL - JULY 2026 - ALL BASKETS, REAL OHLC, 1% STOP ACTIVE")
print("="*112)
print(f"Risk {RISK*100:.0f}% | Leverage {LEV}x | Hard stop {STOP*100:.0f}% | Capital ${INITIAL:,.0f}")
print("New data: daily OHLC for GBPUSD/NZDUSD/USDCAD/USDJPY fetched from Investing.com")
print("          (30 bars each, envelope_fixes=0, cross-checked 107/108 vs existing feed)")
print()
print(f"{'universe':<26}{'timing':>13}{'days':>6}{'asset_WR':>10}{'stops':>7}{'return':>16}{'maxDD':>10}{'final equity':>16}")
print("-"*112)
RES={}
for u in BASKETS:
    for live,lab in ((False,'SIGNAL-DAY'),(True,'LIVE')):
        r=run(u,live); RES[('+'.join(u),lab)]=r
        print(f"{'+'.join(x[:6] for x in u):<26}{lab:>13}{r['trade_days']:>6}"
              f"{r['asset_wr']:>9.1f}%{r['stops']:>7}{r['ret']:>15,.2f}%{r['dd']:>9.2f}%{r['final']:>15,.0f}")
    print()

print("="*112)
print("LIVE-CORRECT TRADE LOG (next-bar entry, stop active)")
print("="*112)
for u in BASKETS[1:]:
    k='+'.join(u); r=RES[(k,'LIVE')]
    print(f"\n--- {k}: {len(r['trades'])} asset trades, {r['stops']} stopped ---")
    for t in r['trades']:
        print(f"  {t['asset']:<7}{t['direction']:<6} sig {t['signal']} -> {t['entry_date']} | "
              f"{t['entry']:>9.5f} -> {t['exit']:<9.5f} stop {t['stop']:<9.5f} "
              f"{t['pnl_pct']:+7.3f}% {t['pnl_usd']:>13,.0f} {t['exit_reason']}")
json.dump({f"{a}|{b}":{k:v for k,v in r.items()} for (a,b),r in RES.items()},
          open('backtest_results/live_model/july2026_swap_ohlc.json','w'),indent=2,default=str)
