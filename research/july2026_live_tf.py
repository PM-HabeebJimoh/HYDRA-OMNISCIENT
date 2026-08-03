#!/usr/bin/env python3
"""
AGBA METTA MODEL - JULY 2026 - DAILY / 4H / 1H
LIVE-CORRECT TIMING (the fix): a signal cannot be traded before it exists.

  bar i CLOSES -> alignment tested on bar i's close vs bar i's open
               -> ENTER at bar i+1 OPEN
               -> 1% hard stop from the ACTUAL entry price, checked on bar i+1 high/low
               -> EXIT at bar i+1 CLOSE unless stopped

Contrast run ("SIGNAL-DAY") reproduces the original engine's entry_date==exit_date
so the difference is visible side by side.

Regime  : real yield > 0.7 CONTRACTION/SHORT, < -0.1 EXPANSION/LONG, else STABILITY
Sizing  : risk 0.20 of equity, equal weight /3, 500x, per src/engine.py
"""
import json, sys, glob, datetime, collections
import numpy as np
sys.path.insert(0, 'scripts')
from intraday_engine import load_1h, resample_4h

RISK, LEV, STOP, INITIAL = 0.20, 500, 0.01, 100000.0
A = ('gold','eur','aud')
utc = lambda t: datetime.datetime.fromtimestamp(int(t), datetime.timezone.utc)

# real yield by date (regime input)
RY = {}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items():
        if 'real_yield' in row: RY[dt] = row['real_yield']

def regime_of(y):
    if y is None: return 'NO_YIELD', 0
    if y > 0.7:  return 'CONTRACTION', -1
    if y < -0.1: return 'EXPANSION', 1
    return 'STABILITY', 0

p1 = load_1h(); p4 = resample_4h(p1)
def to_daily(p):
    B = collections.defaultdict(dict)
    for ts in sorted(p):
        b = ts - (ts % 86400)
        for a in A:
            d = p[ts][a]
            if a not in B[b]: B[b][a] = dict(d)
            else:
                x = B[b][a]; x['high']=max(x['high'],d['high'])
                x['low']=min(x['low'],d['low']); x['close']=d['close']
    return {t:v for t,v in B.items() if len(v)==3}
PAN = {'DAILY': to_daily(p1), '4H': p4, '1H': p1}

def run(panel, live=True, month='2026-07'):
    keys = sorted(panel)
    equity = INITIAL; trades = []; eq = [INITIAL]; rets = []; days = set()
    for i in range(len(keys)-1):
        sk = keys[i]; ek = keys[i+1] if live else keys[i]
        stamp = utc(ek)
        if stamp.strftime('%Y-%m') != month: continue
        y = RY.get(utc(sk).strftime('%Y-%m-%d'))
        reg, direction = regime_of(y)
        if direction == 0: continue
        s = panel[sk]
        if direction == -1 and not all(s[a]['close'] < s[a]['open'] for a in A): continue
        if direction ==  1 and not all(s[a]['close'] > s[a]['open'] for a in A): continue
        e_ = panel[ek]
        pos = equity * RISK / 3
        bar_pnl = 0.0
        for a in A:
            b = e_[a]; entry = b['open']
            sp = entry*(1+STOP) if direction==-1 else entry*(1-STOP)
            ex, reason, hit = b['close'], 'CLOSE', False
            if direction == -1 and b['high'] >= sp: ex, reason, hit = sp, 'STOP_LOSS', True
            if direction ==  1 and b['low']  <= sp: ex, reason, hit = sp, 'STOP_LOSS', True
            pnl_pct = (entry-ex)/entry if direction==-1 else (ex-entry)/entry
            usd = pnl_pct * pos * LEV
            bar_pnl += usd
            trades.append(dict(asset={'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}[a],
                direction='SHORT' if direction==-1 else 'LONG',
                signal_bar=utc(sk).strftime('%Y-%m-%d %H:%M'),
                entry_bar=stamp.strftime('%Y-%m-%d %H:%M'),
                entry=entry, exit=ex, stop=sp, pnl_pct=pnl_pct*100, pnl_usd=usd,
                exit_reason=reason, regime=reg, stop_hit=hit))
        prev = equity; equity += bar_pnl
        rets.append(bar_pnl/prev if prev>0 else 0)
        eq.append(equity); days.add(stamp.strftime('%Y-%m-%d'))
        if equity <= 0:
            equity = 0.0; break
    e = np.array(eq); pk = np.maximum.accumulate(e)
    dd = ((e-pk)/pk).min()*100
    nbars = len(rets)
    wins = sum(1 for r in rets if r > 0)
    aw = sum(1 for t in trades if t['pnl_usd'] > 0)
    gp = sum(t['pnl_usd'] for t in trades if t['pnl_usd']>0)
    gl = -sum(t['pnl_usd'] for t in trades if t['pnl_usd']<0)
    pf = gp/gl if gl>0 else float('inf')
    r = np.array(rets)
    ann = {'DAILY':252,'4H':252*6,'1H':252*24}
    return dict(trades=trades, final=equity, ret=(equity/INITIAL-1)*100,
        bars=nbars, bar_wins=wins, bar_wr=wins/nbars*100 if nbars else 0,
        trade_days=len(days), asset_trades=len(trades), asset_wins=aw,
        asset_wr=aw/len(trades)*100 if trades else 0, pf=pf, dd=dd,
        stops=sum(1 for t in trades if t['stop_hit']), rets=r)

print("="*104)
print("AGBA METTA MODEL - JULY 2026 - DAILY / 4H / 1H")
print("="*104)
print("Universe: XAUUSD / EURUSD / AUDUSD   (the only assets with 1H data in this repo)")
print(f"Risk/Trade {RISK*100:.0f}% | Leverage {LEV}x | Hard Stop {STOP*100:.0f}% | Capital ${INITIAL:,.0f}")
print("Data: Investing.com 1H, 4H resampled from 1H. EUR/AUD 1H ends 2026-07-27 (provider gap).")
print()
hdr = f"{'TF':>6} {'timing':>12} {'bars':>5} {'bar_WR':>8} {'trade_days':>11} {'asset_WR':>9} {'stops':>6} {'return':>16} {'maxDD':>10} {'final equity':>16}"
print(hdr); print("-"*104)
RES = {}
for tf in ('DAILY','4H','1H'):
    for live,lab in ((False,'SIGNAL-DAY'),(True,'LIVE next-bar')):
        r = run(PAN[tf], live=live)
        RES[(tf,lab)] = r
        pf = 'inf' if r['pf']==float('inf') else f"{r['pf']:.2f}"
        print(f"{tf:>6} {lab:>12} {r['bars']:5d} {r['bar_wr']:7.1f}% {r['trade_days']:11d} "
              f"{r['asset_wr']:8.1f}% {r['stops']:6d} {r['ret']:15,.2f}% {r['dd']:9.2f}% {r['final']:15,.0f}")
    print()

print("="*104)
print("LIVE-CORRECT TRADE LOG (next-bar entry)")
print("="*104)
for tf in ('DAILY','4H','1H'):
    r = RES[(tf,'LIVE next-bar')]
    print(f"\n--- {tf}: {len(r['trades'])} asset trades over {r['bars']} signal bars, {r['stops']} stopped ---")
    for t in r['trades'][:24]:
        print(f"  {t['asset']:<7}{t['direction']:<6} signal {t['signal_bar']:>16} -> entry {t['entry_bar']:>16} "
              f"| {t['entry']:>10.5f} -> {t['exit']:<10.5f} {t['pnl_pct']:+7.3f}% {t['pnl_usd']:>14,.0f} {t['exit_reason']}")
    if len(r['trades'])>24: print(f"  ... {len(r['trades'])-24} more (full log in JSON)")

json.dump({f"{k[0]}|{k[1]}": {kk:(vv.tolist() if hasattr(vv,'tolist') else vv)
           for kk,vv in v.items() if kk!='rets'} for k,v in RES.items()},
          open('backtest_results/live_model/july2026_daily_4h_1h.json','w'), indent=2, default=str)
