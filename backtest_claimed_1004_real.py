#!/usr/bin/env python3
"""
HYDRA-S3-MAX | REAL DATA - REPLICATE CLAIMED 1004% ROI
========================================================
Test the exact parameters from JULY_2026_FULL_TILL_TODAY_REAL.md:
- 500x leverage
- 20% risk per trade  
- No stop loss (hold to close)
- Sum of favorable returns = 10.04%
- Expected: 10.04% * 500 * 0.2 = 1004% ROI
"""

import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
log = logging.getLogger('HYDRA-REAL-1004')

# REAL DATA from JULY_2026_FULL_TILL_TODAY_REAL.md
REAL_TRADE_DAYS = [
    {
        "date": "2026-07-07",
        "yield": 2.30,
        "regime": "CONTRACTION",
        "assets": {
            "XAUUSD": {"ret": -1.53, "direction": -1},  # SHORT
            "EURUSD": {"ret": -0.33, "direction": -1},
            "AUDUSD": {"ret": -0.45, "direction": -1},
        }
    },
    {
        "date": "2026-07-13",
        "yield": 2.36,
        "regime": "CONTRACTION",
        "assets": {
            "XAUUSD": {"ret": -2.80, "direction": -1},
            "EURUSD": {"ret": -0.31, "direction": -1},
            "AUDUSD": {"ret": -0.55, "direction": -1},
        }
    },
    {
        "date": "2026-07-16",
        "yield": 2.35,
        "regime": "CONTRACTION",
        "assets": {
            "XAUUSD": {"ret": -2.12, "direction": -1},
            "EURUSD": {"ret": -0.20, "direction": -1},
            "AUDUSD": {"ret": -0.14, "direction": -1},
        }
    },
    {
        "date": "2026-07-17",
        "yield": 2.31,
        "regime": "CONTRACTION",
        "assets": {
            "XAUUSD": {"ret": +1.06, "direction": -1},  # LOSS for SHORT
            "EURUSD": {"ret": -0.03, "direction": -1},
            "AUDUSD": {"ret": -0.21, "direction": -1},
        }
    },
    {
        "date": "2026-07-23",
        "yield": 2.43,
        "regime": "CONTRACTION",
        "assets": {
            "XAUUSD": {"ret": -1.88, "direction": -1},
            "EURUSD": {"ret": -0.26, "direction": -1},
            "AUDUSD": {"ret": -0.29, "direction": -1},
        }
    },
]

# CLAIMED PARAMETERS
LEVERAGE = 500
RISK_PER_TRADE = 0.20      # 20%
INITIAL_CAPITAL = 100_000.0
ASSETS_PER_DAY = 3

def run_claimed_1004_backtest():
    """Run with exact claimed parameters: 500x leverage, 20% risk, no stop loss."""
    
    equity = INITIAL_CAPITAL
    equity_curve = []
    all_trades = []
    
    print("=" * 70)
    print("HYDRA-S3-MAX | REAL DATA - CLAIMED 1004% PARAMETERS")
    print(f"Leverage: {LEVERAGE}x | Risk: {RISK_PER_TRADE*100}% | No Stop Loss")
    print("=" * 70)
    
    for day in REAL_TRADE_DAYS:
        date_str = day["date"]
        log.info(f"\n>>> {date_str} | Yield: {day['yield']}% | {day['regime']}")
        
        day_pnl = 0.0
        day_trades = 0
        day_wins = 0
        
        # Position size per asset: risk 20% / (leverage * expected_move)
        # But with NO stop loss, we just use 20% risk = position_size * leverage * avg_move
        # The claimed formula: ROI = sum_returns * leverage * risk_pct
        # So position = equity * risk_pct / (leverage * expected_move_pct)
        
        # Actually, let's just follow: each trade risks 20% of equity
        # With 500x leverage, a 1% move = 500% PnL
        # To risk 20%, the adverse move tolerance = 20% / 500 = 0.04%
        # But NO stop loss means we don't enforce this
        
        # Position per asset = equity * (RISK_PER_TRADE / ASSETS_PER_DAY) 
        # Actually, let's use the compounding approach from their math
        
        for symbol, info in day["assets"].items():
            ret = info["ret"] / 100  # Convert to decimal
            direction = info["direction"]
            
            # Position: risk 20%/3 = 6.67% per asset per day
            # With 500x leverage, PnL = position * leverage * ret * direction
            position_per_asset = equity * (RISK_PER_TRADE / ASSETS_PER_DAY)
            
            pnl = position_per_asset * LEVERAGE * ret * direction
            pnl_pct = (pnl / equity) * 100
            
            is_win = pnl > 0
            
            all_trades.append({
                "date": date_str,
                "asset": symbol,
                "direction": "SHORT" if direction == -1 else "LONG",
                "ret_pct": info["ret"],
                "position": position_per_asset,
                "leverage": LEVERAGE,
                "pnl_usd": pnl,
                "pnl_pct": pnl_pct,
                "win": is_win,
            })
            
            day_pnl += pnl
            day_trades += 1
            if is_win: day_wins += 1
            
            log.info(f"  {symbol} {'SHORT' if direction==-1 else 'LONG'}: "
                     f"Ret {info['ret']:+.2f}% | Pos ${position_per_asset:,.0f} | "
                     f"PnL ${pnl:+,.0f} ({pnl_pct:+.2f}%) | {'WIN' if is_win else 'LOSS'}")
        
        equity += day_pnl
        
        equity_curve.append({
            "date": date_str,
            "equity": equity,
            "daily_pnl": day_pnl,
            "trades": day_trades,
            "wins": day_wins,
            "losses": day_trades - day_wins,
        })
        
        log.info(f"  DAY: PnL ${day_pnl:+,.0f} | Equity ${equity:,.0f} | {day_wins}W/{day_trades-day_wins}L")
    
    equity_df = pd.DataFrame(equity_curve)
    equity_df['date'] = pd.to_datetime(equity_df['date'])
    equity_df = equity_df.set_index('date')
    
    return all_trades, equity_df, equity


def calculate_metrics(trades, equity_df, initial_capital):
    wins = sum(1 for t in trades if t["win"])
    losses = len(trades) - wins
    win_rate = wins / len(trades) * 100 if trades else 0
    
    total_return = (equity_df['equity'].iloc[-1] / initial_capital - 1) * 100
    
    daily_rets = equity_df['equity'].pct_change().dropna()
    sharpe = daily_rets.mean() / (daily_rets.std() + 1e-9) * np.sqrt(252) if len(daily_rets) > 1 else 0
    
    peak = equity_df['equity'].expanding().max()
    dd = (equity_df['equity'] - peak) / peak
    max_dd = dd.min() * 100
    
    win_pcts = [t["pnl_pct"] for t in trades if t["win"]]
    loss_pcts = [t["pnl_pct"] for t in trades if not t["win"]]
    
    return {
        "total_return_pct": round(total_return, 2),
        "total_trades": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(win_rate, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "avg_win_pct": round(np.mean(win_pcts), 2) if win_pcts else 0,
        "avg_loss_pct": round(np.mean(loss_pcts), 2) if loss_pcts else 0,
        "final_equity": round(equity_df['equity'].iloc[-1], 2),
        "initial_capital": initial_capital,
    }


def main():
    trades, equity_df, final_equity = run_claimed_1004_backtest()
    metrics = calculate_metrics(trades, equity_df, INITIAL_CAPITAL)
    
    print("\n" + "=" * 70)
    print("📊 CLAIMED 1004% PARAMETERS WITH REAL DATA")
    print("=" * 70)
    print(f"  Initial Capital:      ${INITIAL_CAPITAL:,.0f}")
    print(f"  Final Equity:         ${metrics['final_equity']:,.0f}")
    print(f"  Total Return:         {metrics['total_return_pct']:+.2f}%")
    print(f"  Total Trades:         {metrics['total_trades']}")
    print(f"  Wins:                 {metrics['wins']}")
    print(f"  Losses:               {metrics['losses']}")
    print(f"  Win Rate:             {metrics['win_rate_pct']:.2f}%")
    print(f"  Max Drawdown:         {metrics['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio:         {metrics['sharpe_ratio']:.2f}")
    print(f"  Avg Win:              {metrics['avg_win_pct']:+.2f}%")
    print(f"  Avg Loss:             {metrics['avg_loss_pct']:+.2f}%")
    print("=" * 70)
    
    goal_wr = metrics['win_rate_pct'] >= 80
    goal_roi = metrics['total_return_pct'] >= 1000
    goal_dd = metrics['max_drawdown_pct'] > -20
    
    print(f"\n🎯 GOAL CHECK:")
    print(f"  WR > 80%:        {'✅ PASS' if goal_wr else '❌ FAIL'} ({metrics['win_rate_pct']:.1f}%)")
    print(f"  ROI > 1000%:     {'✅ PASS' if goal_roi else '❌ FAIL'} ({metrics['total_return_pct']:.1f}%)")
    print(f"  DD < 20%:        {'✅ PASS' if goal_dd else '❌ FAIL'} ({metrics['max_drawdown_pct']:.1f}%)")
    print(f"  OVERALL:         {'✅ ALL GOALS MET' if (goal_wr and goal_roi and goal_dd) else '❌ NOT ACHIEVED'}")
    
    # Calculate sum of returns
    sum_ret = sum(t["ret_pct"] for t in trades if t["win"]) + sum(t["ret_pct"] for t in trades if not t["win"])
    print(f"\n📊 REAL MARKET SUMMARY:")
    print(f"  Sum of daily returns (all): {sum_ret:.2f}%")
    print(f"  Claimed formula: {sum_ret:.2f}% × {LEVERAGE} × {RISK_PER_TRADE} = {sum_ret/100 * LEVERAGE * RISK_PER_TRADE * 100:.1f}%")
    print(f"  Actual achieved: {metrics['total_return_pct']:.1f}%")
    
    # Save
    import os
    os.makedirs('/home/user/HYDRA-OMNISCIENT/backtest_results', exist_ok=True)
    
    pd.DataFrame(trades).to_csv(
        '/home/user/HYDRA-OMNISCIENT/backtest_results/trades_claimed_1004_real.csv', 
        index=False
    )
    equity_df.to_csv('/home/user/HYDRA-OMNISCIENT/backtest_results/equity_claimed_1004_real.csv')
    
    with open('/home/user/HYDRA-OMNISCIENT/backtest_results/summary_claimed_1004_real.json', 'w') as f:
        json.dump({
            "model": "HYDRA-S3-MAX",
            "test": "claimed_1004_parameters_real_data",
            "period": "2026-07-07 to 2026-07-23 (5 real trade days)",
            "parameters": {
                "leverage": LEVERAGE,
                "risk_per_trade": RISK_PER_TRADE,
                "stop_loss": None,
            },
            "metrics": metrics,
            "goals_met": goal_wr and goal_roi and goal_dd,
            "note": "Test of claimed 1004% formula with REAL July 2026 market data"
        }, f, indent=2, default=str)
    
    print("\n📁 Saved to backtest_results/")


if __name__ == '__main__':
    main()