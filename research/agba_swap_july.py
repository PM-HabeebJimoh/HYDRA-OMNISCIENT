#!/usr/bin/env python3
"""
AGBA METTA MODEL - BASKET SUBSTITUTION BACKTEST
July 2026. Universe XAUUSD/EURUSD/AUDUSD replaced by each candidate basket.

Runs the model's OWN mechanics, exactly as src/engine.py implements them:
  Regime      : real yield > 0.7 = CONTRACTION (SHORT)
                real yield < -0.1 = EXPANSION (LONG)
                otherwise STABILITY = no trade
  Alignment   : CONTRACTION requires ALL assets close < open
                EXPANSION requires ALL assets close > open
                misaligned = SKIP the day
  Entry       : that SAME day's OPEN   (entry_date == exit_date in the model)
  Exit        : that SAME day's CLOSE, unless the 1% hard stop is hit intraday
  Sizing      : risk_per_trade_pct 0.20 of equity, equal weight across 3 assets,
                leverage applied to each asset's position_size
Metrics reported are the model's own: trade_days, day/asset win rate,
profit_factor, max_drawdown_pct, sharpe_ratio.
"""
import json, glob
import numpy as np

RISK, LEV, STOP = 0.20, 500, 0.01
INITIAL = 100000.0

# ---- load real OHLC ----
D = {}
for dt, row in json.load(open('data/market_data_spot.json')).items():
    D.setdefault(dt, {}).update(row)
NAME = {'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}
for dt in list(D):
    for k, v in list(D[dt].items()):
        if k in NAME: D[dt][NAME[k]] = v
for f in glob.glob('data/raw/xpairs/*.json'):
    j = json.load(open(f))
    for i, dt in enumerate(j['dates']):
        D.setdefault(dt, {})[j['symbol']] = {'open': j['o'][i], 'close': j['c'][i]}

def has_hl(sym, dt):
    return 'high' in D[dt][sym] and 'low' in D[dt][sym]

def regime_of(y):
    if y > 0.7:  return 'CONTRACTION', -1
    if y < -0.1: return 'EXPANSION', 1
    return 'STABILITY', 0

def run(universe, month='2026-07'):
    dates = sorted(d for d in D if d.startswith(month)
                   and all(s in D[d] for s in universe) and 'real_yield' in D[d])
    equity = INITIAL; peak = INITIAL
    trades = []; eq_rows = []; daily_rets = []
    for dt in dates:
        md = D[dt]
        reg_name, direction = regime_of(md['real_yield'])
        aligned = False
        if direction == -1:
            aligned = all(md[s]['close'] < md[s]['open'] for s in universe)
        elif direction == 1:
            aligned = all(md[s]['close'] > md[s]['open'] for s in universe)
        if direction == 0 or not aligned:
            eq_rows.append((dt, equity, 0.0, 0.0, reg_name, False, aligned))
            daily_rets.append(0.0); continue

        position_per_asset = equity * RISK / len(universe)
        day_pnl = 0.0
        for sym in universe:
            o = md[sym]; entry = o['open']
            stop_price = entry*(1+STOP) if direction == -1 else entry*(1-STOP)
            exit_price = o['close']; reason = 'CLOSE'; stop_hit = False
            if has_hl(sym, dt):
                if direction == -1 and o['high'] >= stop_price:
                    exit_price, reason, stop_hit = stop_price, 'STOP_LOSS', True
                elif direction == 1 and o['low'] <= stop_price:
                    exit_price, reason, stop_hit = stop_price, 'STOP_LOSS', True
            pnl_pct = (entry-exit_price)/entry if direction == -1 else (exit_price-entry)/entry
            notional = position_per_asset*LEV
            pnl_usd = pnl_pct*notional
            day_pnl += pnl_usd
            trades.append(dict(trade_id=f"{sym}-{dt}-{reason}", asset=sym,
                direction='SHORT' if direction==-1 else 'LONG', entry_price=entry,
                exit_price=exit_price, stop_price=stop_price, entry_date=dt, exit_date=dt,
                position_size=position_per_asset, leverage=LEV, pnl_pct=pnl_pct*100,
                pnl_usd=pnl_usd, exit_reason=reason, regime=reg_name, stop_hit=stop_hit))
        prev = equity; equity += day_pnl
        daily_rets.append(day_pnl/prev if prev>0 else 0.0)
        peak = max(peak, equity)
        eq_rows.append((dt, equity, day_pnl, day_pnl/prev*100 if prev>0 else 0, reg_name, True, True))

    eq = np.array([r[1] for r in eq_rows]) if eq_rows else np.array([INITIAL])
    pk = np.maximum.accumulate(np.concatenate([[INITIAL], eq]))[1:]
    max_dd = ((eq-pk)/pk).min()*100 if len(eq) else 0.0
    tds = [r for r in eq_rows if r[5]]
    day_wins = sum(1 for r in tds if r[2] > 0)
    a_wins = sum(1 for t in trades if t['pnl_usd'] > 0)
    gp = sum(t['pnl_usd'] for t in trades if t['pnl_usd'] > 0)
    gl = -sum(t['pnl_usd'] for t in trades if t['pnl_usd'] < 0)
    pf = (gp/gl) if gl > 0 else float('inf')
    dr = np.array(daily_rets)
    sharpe = dr.mean()/(dr.std()+1e-9)*np.sqrt(252) if len(dr) > 1 else 0.0
    return dict(universe=universe, dates=dates, trades=trades, eq_rows=eq_rows,
        final_equity=equity, total_return_pct=(equity/INITIAL-1)*100,
        trade_days=len(tds), day_wins=day_wins, day_losses=len(tds)-day_wins,
        day_win_rate_pct=day_wins/len(tds)*100 if tds else 0.0,
        asset_trades=len(trades), asset_wins=a_wins, asset_losses=len(trades)-a_wins,
        asset_win_rate_pct=a_wins/len(trades)*100 if trades else 0.0,
        profit_factor=pf, max_drawdown_pct=max_dd, sharpe_ratio=sharpe)

BASKETS = [('XAUUSD','EURUSD','AUDUSD'),
           ('AUDUSD','GBPUSD','USDCAD'),
           ('EURUSD','AUDUSD','USDCAD'),
           ('GBPUSD','NZDUSD','USDCAD'),
           ('NZDUSD','USDCAD','USDJPY')]

out = {}
for u in BASKETS:
    r = run(u); out['+'.join(u)] = r
    print("="*80)
    print("AGBA METTA MODEL - REAL OHLC BACKTEST")
    print("="*80)
    print(f"Universe: {' / '.join(u)}")
    print(f"Period: 2026-07-01 to 2026-07-31")
    print(f"Initial Capital: ${INITIAL:,.0f}")
    print(f"Risk/Trade: {RISK*100}% | Leverage: {LEV}x")
    print(f"Hard Stop: {STOP*100}% | Entry: open | Exit: close")
    hl = all(has_hl(s, r['dates'][0]) for s in u) if r['dates'] else False
    print(f"Stop evaluable (high/low present): {hl}")
    print(f"Loaded {len(r['dates'])} trading days of real OHLC data")
    print()
    print("AGBA METTA MODEL - BACKTEST RESULTS")
    print("-"*80)
    print(f"  Initial Capital:      ${INITIAL:,.0f}")
    print(f"  Final Equity:         ${r['final_equity']:,.2f}")
    print(f"  Total Return:         {r['total_return_pct']:+.2f}%")
    print(f"  Trade Days:           {r['trade_days']}")
    print(f"  Day Win Rate:         {r['day_win_rate_pct']:.2f}% ({r['day_wins']}/{r['trade_days']})")
    print(f"  Asset Win Rate:       {r['asset_win_rate_pct']:.2f}% ({r['asset_wins']}/{r['asset_trades']})")
    pfs = 'inf' if r['profit_factor']==float('inf') else f"{r['profit_factor']:.2f}"
    print(f"  Profit Factor:        {pfs}")
    print(f"  Max Drawdown:         {r['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio:         {r['sharpe_ratio']:.2f}")
    print()
    print("  GOAL CHECK (model's own thresholds):")
    print(f"    Day WR > 80%:       {'PASS' if r['day_win_rate_pct']>=80 else 'FAIL'} ({r['day_win_rate_pct']:.1f}%)")
    print(f"    ROI > 1000%:        {'PASS' if r['total_return_pct']>=1000 else 'FAIL'} ({r['total_return_pct']:.1f}%)")
    print(f"    DD < 20%:           {'PASS' if r['max_drawdown_pct']>-20 else 'FAIL'} ({r['max_drawdown_pct']:.1f}%)")
    print()
    if r['trades']:
        print("  ALL TRADES:")
        print("  "+"-"*116)
        print(f"  {'asset':<8}{'dir':<7}{'entry':>11}{'exit':>11}{'stop':>11}{'date':>12}{'pnl_pct':>10}{'pnl_usd':>15}{'exit_reason':>13}{'regime':>13}")
        for t in r['trades']:
            print(f"  {t['asset']:<8}{t['direction']:<7}{t['entry_price']:>11.5f}{t['exit_price']:>11.5f}"
                  f"{t['stop_price']:>11.5f}{t['entry_date']:>12}{t['pnl_pct']:>9.4f}%{t['pnl_usd']:>15,.2f}"
                  f"{t['exit_reason']:>13}{t['regime']:>13}")
    else:
        print("  ALL TRADES: none - alignment never confirmed in July 2026")
    print()

print("="*80)
print("COMPARISON - JULY 2026")
print("="*80)
print(f"{'universe':<30}{'trade_days':>11}{'day_WR':>9}{'asset_WR':>10}{'return':>14}{'maxDD':>9}{'sharpe':>8}")
for k, r in out.items():
    print(f"{k:<30}{r['trade_days']:>11}{r['day_win_rate_pct']:>8.1f}%{r['asset_win_rate_pct']:>9.1f}%"
          f"{r['total_return_pct']:>13.2f}%{r['max_drawdown_pct']:>8.2f}%{r['sharpe_ratio']:>8.2f}")
json.dump({k:{kk:vv for kk,vv in v.items() if kk not in ('eq_rows',)} for k,v in out.items()},
          open('backtest_results/live_model/july2026_basket_swap.json','w'), indent=2, default=str)
