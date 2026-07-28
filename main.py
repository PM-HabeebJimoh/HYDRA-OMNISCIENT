#!/usr/bin/env python3
"""
Agba Metta Model - Main Backtest Entry Point
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config_loader import load_config
from src.data_loader import load_market_data_for_backtest
from src.engine import run_backtest

from src.models import Trade, DailyEquity


def run_agba_metta_backtest():
    """Run complete Agba Metta Model backtest"""
    
    print("=" * 80)
    print("AGBA METTA MODEL - REAL OHLC BACKTEST")
    print("=" * 80)
    
    # Load configuration
    config = load_config()
    print(f"Model: {config.model.name} v{config.model.version}")
    print(f"Period: {config.backtest.start_date} to {config.backtest.end_date}")
    print(f"Initial Capital: ${config.backtest.initial_capital:,.0f}")
    print(f"Risk/Trade: {config.position_sizing.risk_per_trade_pct*100}% | Leverage: {config.position_sizing.leverage}x")
    print(f"Hard Stop: {config.risk.hard_stop_pct*100}% | Max DD: {config.risk.max_drawdown_pct*100}%")
    print()
    
    # Load real market data
    print("Loading REAL OHLC data from verified sources...")
    market_data = load_market_data_for_backtest(
        config.backtest.start_date, 
        config.backtest.end_date
    )
    print(f"Loaded {len(market_data)} trading days of real OHLC data")
    print()
    
    # Run backtest
    print("Running backtest...")
    trades, equity_curve, metrics = run_backtest(config, market_data)
    
    # Print results
    print("\n" + "=" * 80)
    print("AGBA METTA MODEL - BACKTEST RESULTS")
    print("=" * 80)
    print(f"  Initial Capital:      ${config.backtest.initial_capital:,.0f}")
    print(f"  Final Equity:         ${metrics['final_equity']:,.0f}")
    print(f"  Total Return:         {metrics['total_return_pct']:+.2f}%")
    print(f"  Trade Days:           {metrics['trade_days']}")
    print(f"  Day Win Rate:         {metrics['day_win_rate_pct']:.2f}% ({metrics['day_wins']}/{metrics['trade_days']})")
    print(f"  Asset Win Rate:       {metrics['asset_win_rate_pct']:.2f}% ({metrics['asset_wins']}/{metrics['asset_trades']})")
    print(f"  Profit Factor:        {metrics['profit_factor']}")
    print(f"  Max Drawdown:         {metrics['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio:         {metrics['sharpe_ratio']:.2f}")
    print("=" * 80)
    
    # Goal check
    goal_wr = metrics['day_win_rate_pct'] >= 80
    goal_roi = metrics['total_return_pct'] >= 1000
    goal_dd = metrics['max_drawdown_pct'] > -20
    
    print(f"\nGOAL CHECK:")
    print(f"  Day WR > 80%:       {'PASS' if goal_wr else 'FAIL'} ({metrics['day_win_rate_pct']:.1f}%)")
    print(f"  ROI > 1000%:        {'PASS' if goal_roi else 'FAIL'} ({metrics['total_return_pct']:.1f}%)")
    print(f"  DD < 20%:           {'PASS' if goal_dd else 'FAIL'} ({metrics['max_drawdown_pct']:.1f}%)")
    print(f"  OVERALL:            {'ALL GOALS MET' if (goal_wr and goal_roi and goal_dd) else 'NOT ACHIEVED'}")
    
    # Print all trades
    print("\nALL TRADES:")
    print("-" * 120)
    for t in trades:
        direction_str = "LONG" if t.direction == 1 else "SHORT"
        print(f"  {t.entry_date} | {t.asset:7s} | {direction_str:5s} | "
              f"Entry: {t.entry_price:>10.5f} | Exit: {t.exit_price:>10.5f} | "
              f"Stop: {t.stop_price:>10.5f} | "
              f"Ret: {t.pnl_pct*100:+7.2f}% | PnL: ${t.pnl_usd:+12,.0f} | "
              f"{t.exit_reason:10s} | {'WIN' if t.pnl_usd > 0 else 'LOSS'} | Equity: ${t.equity_after:>12,.0f}")
    
    # Save results
    output_dir = Path(__file__).parent / "backtest_results"
    output_dir.mkdir(exist_ok=True)
    
    # Save trades
    trades_df = pd.DataFrame([t.to_dict() for t in trades])
    trades_path = output_dir / "trades_agba_metta.csv"
    trades_df.to_csv(trades_path, index=False)
    print(f"\nTrades saved to: {trades_path}")
    
    # Save equity curve
    equity_df = pd.DataFrame([e.to_dict() for e in equity_curve])
    equity_path = output_dir / "equity_agba_metta.csv"
    equity_df.to_csv(equity_path, index=False)
    print(f"Equity curve saved to: {equity_path}")
    
    # Save summary
    summary = {
        "model": "Agba Metta Model",
        "version": "1.0.0",
        "period": f"{config.backtest.start_date} to {config.backtest.end_date}",
        "config": {
            "risk_per_trade_pct": config.position_sizing.risk_per_trade_pct,
            "leverage": config.position_sizing.leverage,
            "hard_stop_pct": config.risk.hard_stop_pct,
            "max_drawdown_pct": config.risk.max_drawdown_pct,
            "alignment_enabled": True,
            "entry": "open",
            "exit": "close",
            "stop_loss_type": "hard"
        },
        "data_sources": {
            "gold": "COMEX front-month gold future (Yahoo Finance GC=F), daily OHLC",
            "eurusd": "CME front-month Euro FX future (Yahoo Finance 6E=F), daily OHLC",
            "audusd": "CME front-month AUD future (Yahoo Finance 6A=F), daily OHLC",
            "real_yield": "FRED DFII10 (10Y TIPS constant-maturity real yield)"
        },
        "metrics": metrics,
        "goals_met": goal_wr and goal_roi and goal_dd
    }
    
    summary_path = output_dir / "summary_agba_metta.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"Summary saved to: {summary_path}")
    
    print(f"\n{'ALL GOALS ACHIEVED!' if (goal_wr and goal_roi and goal_dd) else 'GOALS NOT MET'}")
    
    return trades, equity_curve, metrics


if __name__ == "__main__":
    trades, equity_curve, metrics = run_agba_metta_backtest()