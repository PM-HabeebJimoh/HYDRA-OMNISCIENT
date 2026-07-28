"""
Agba Metta Model - Core Execution Engine
Standalone execution engine with alignment filter, position sizing, and risk management
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from src.models import (
    OHLCData, MarketData, Trade, DailyEquity, Position,
    Regime, Direction, ExitReason, AlignmentResult
)
from src.config_loader import AgbaMettaConfig

logger = logging.getLogger('AGBA-METTA-ENGINE')


class AlignmentFilter:
    """The 'Agba' Logic - Only trade when ALL assets confirm regime direction"""

    def __init__(self, config: AgbaMettaConfig):
        self.enabled = config.alignment.enabled
        self.contraction_requires_all_down = config.alignment.contraction_requires_all_down
        self.expansion_requires_all_up = config.alignment.expansion_requires_all_up

    def check_alignment(self, market_data: MarketData, regime: Regime) -> AlignmentResult:
        """Check if ALL assets confirm regime direction"""
        if not self.enabled:
            return AlignmentResult(True, "Alignment filter disabled")

        if regime == Regime.CONTRACTION:
            # SHORT: all must close lower than open
            gold_down = market_data.gold.close < market_data.gold.open
            eur_down = market_data.eur.close < market_data.eur.open
            aud_down = market_data.aud.close < market_data.aud.open

            aligned = gold_down and eur_down and aud_down
            reason = f"Gold: {'↓' if gold_down else '↑'}, EUR: {'↓' if eur_down else '↑'}, AUD: {'↓' if aud_down else '↑'}"

        elif regime == Regime.EXPANSION:
            # LONG: all must close higher than open
            gold_up = market_data.gold.close > market_data.gold.open
            eur_up = market_data.eur.close > market_data.eur.open
            aud_up = market_data.aud.close > market_data.aud.open

            aligned = gold_up and eur_up and aud_up
            reason = f"Gold: {'↑' if gold_up else '↓'}, EUR: {'↑' if eur_up else '↓'}, AUD: {'↑' if aud_up else '↓'}"

        else:
            aligned = False
            reason = "STABILITY regime - no trades"

        return AlignmentResult(aligned, reason)


class RiskManager:
    """The 'Metta' Risk Management Logic"""

    def __init__(self, config: AgbaMettaConfig):
        self.hard_stop_pct = config.risk.hard_stop_pct
        self.max_drawdown_pct = config.risk.max_drawdown_pct
        self.max_daily_loss_pct = config.risk.max_daily_loss_pct
        self.stop_loss_type = config.risk.stop_loss_type
        self.peak_equity = 0.0
        self.daily_start_equity = 0.0

    def calculate_stop_price(self, entry_price: float, direction: int) -> float:
        """Calculate 1% hard stop price"""
        if direction == Direction.SHORT.value:  # SHORT
            return entry_price * (1 + self.hard_stop_pct)
        else:  # LONG
            return entry_price * (1 - self.hard_stop_pct)

    def check_stop_loss(self, entry_price: float, high: float, low: float,
                       direction: int) -> Tuple[bool, float, float]:
        """
        Check if stop loss was hit intraday
        Returns: (hit, stop_price, exit_price)
        """
        if self.stop_loss_type == "none":
            return False, 0.0, 0.0

        stop_price = self.calculate_stop_price(entry_price, direction)

        if direction == Direction.SHORT.value:  # SHORT - stop hit if HIGH >= stop
            hit = high >= stop_price
            exit_price = stop_price if hit else 0.0
        else:  # LONG - stop hit if LOW <= stop
            hit = low <= stop_price
            exit_price = stop_price if hit else 0.0

        return hit, stop_price, exit_price

    def check_max_drawdown(self, equity: float) -> bool:
        """Check if max drawdown exceeded"""
        if equity > self.peak_equity:
            self.peak_equity = equity
        dd = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
        return dd >= self.max_drawdown_pct

    def check_daily_loss_limit(self, equity: float) -> bool:
        """Check if daily loss limit exceeded"""
        if self.daily_start_equity == 0:
            self.daily_start_equity = equity
            return False
        daily_loss = (self.daily_start_equity - equity) / self.daily_start_equity
        return daily_loss >= self.max_daily_loss_pct

    def reset_daily(self, equity: float):
        """Reset daily tracking"""
        self.daily_start_equity = equity
        if equity > self.peak_equity:
            self.peak_equity = equity


class PositionSizer:
    """The 'Metta' Position Sizing Logic"""

    def __init__(self, config: AgbaMettaConfig):
        self.risk_per_trade_pct = config.position_sizing.risk_per_trade_pct
        self.leverage = config.position_sizing.leverage
        self.equal_weight = config.position_sizing.equal_weight
        self.max_assets = config.position_sizing.max_assets_per_trade

    def calculate_position_size(self, equity: float, num_assets: int) -> Tuple[float, float]:
        """
        Returns: (total_position, position_per_asset)
        """
        if num_assets == 0:
            return 0.0, 0.0

        # Cap at max assets
        actual_assets = min(num_assets, self.max_assets)
        total_position = equity * self.risk_per_trade_pct
        position_per_asset = total_position / actual_assets if self.equal_weight else total_position / num_assets

        return total_position, position_per_asset

    def calculate_notional(self, position_per_asset: float) -> float:
        """Calculate notional value with leverage"""
        return position_per_asset * self.leverage


class AgbaMettaEngine:
    """Main Agba Metta Execution Engine"""

    def __init__(self, config: AgbaMettaConfig):
        self.config = config
        self.alignment_filter = AlignmentFilter(config)
        self.risk_manager = RiskManager(config)
        self.position_sizer = PositionSizer(config)
        self.regime_thresholds = {
            'contraction': config.regime.contraction_yield_threshold,
            'expansion': config.regime.expansion_yield_threshold
        }
        self.regime_direction = config.regime_direction
        self.execution_config = config.execution
        # Access regime_direction as dataclass attributes
        self.regime_direction_map = {
            'CONTRACTION': config.regime_direction.CONTRACTION,
            'EXPANSION': config.regime_direction.EXPANSION,
            'STABILITY': config.regime_direction.STABILITY
        }

        # State
        self.equity = config.backtest.initial_capital
        self.initial_capital = config.backtest.initial_capital
        self.open_positions: Dict[str, Position] = {}
        self.closed_trades: List[Trade] = []
        self.equity_curve: List[DailyEquity] = []
        self.risk_manager.peak_equity = config.backtest.initial_capital
        # Circuit-breaker state. Once tripped the engine stops opening new
        # positions for the remainder of the run.
        self.halted = False
        self.halt_reason = None

    def determine_regime(self, real_yield: float) -> Regime:
        """Determine regime from real yield"""
        if real_yield > self.regime_thresholds['contraction']:
            return Regime.CONTRACTION
        elif real_yield < self.regime_thresholds['expansion']:
            return Regime.EXPANSION
        return Regime.STABILITY

    def check_alignment(self, market_data, regime) -> AlignmentResult:
        """Check if all assets align with regime direction"""
        # Handle both Regime enum and string
        regime_str = regime.name if hasattr(regime, 'name') else str(regime)
        
        if regime_str == "STABILITY":
            return AlignmentResult(False, "STABILITY regime")
        
        # Check alignment
        gold_down = market_data.gold.close < market_data.gold.open
        eur_down = market_data.eur.close < market_data.eur.open
        aud_down = market_data.aud.close < market_data.aud.open
        
        if regime_str == "CONTRACTION":
            aligned = gold_down and eur_down and aud_down
            return AlignmentResult(aligned, f"Gold: {'↓' if market_data.gold.close < market_data.gold.open else '↑'}, EUR: {'↓' if market_data.eur.close < market_data.eur.open else '↑'}, AUD: {'↓' if market_data.aud.close < market_data.aud.open else '↑'}")
        else:  # EXPANSION
            gold_up = market_data.gold.close > market_data.gold.open
            eur_up = market_data.eur.close > market_data.eur.open
            aud_up = market_data.aud.close > market_data.aud.open
            aligned = gold_up and eur_up and aud_up
            return AlignmentResult(aligned, f"Gold: {'↑' if market_data.gold.close > market_data.gold.open else '↓'}, EUR: {'↑' if market_data.eur.close > market_data.eur.open else '↓'}, AUD: {'↑' if market_data.aud.close > market_data.aud.open else '↓'}")

    def open_positions_for_day(self, market_data, regime: Regime, date: str) -> List[Trade]:
        """Open positions for aligned assets at the day's open (Agba Metta rule)"""
        trades = []
        # Handle both Regime enum and string
        regime_str = regime.name if hasattr(regime, 'name') else str(regime)
        direction = self.regime_direction_map.get(regime_str, 0)

        if direction == 0:
            return trades

        # Agba Metta alignment: all assets must confirm the regime direction
        alignment = self.alignment_filter.check_alignment(market_data, regime)
        if not alignment.aligned:
            logger.info(f"  {date} | MISALIGNED: {alignment.reason} - SKIPPING")
            return trades

        logger.info(f"  {date} | ALIGNED: {alignment.reason} - ENTERING TRADES")

        # Metta sizing: equal weight across the assets actually traded, capped
        # by max_assets_per_trade from config.
        tradable = self.config.universe.assets[: self.position_sizer.max_assets]
        total_position, position_per_asset = self.position_sizer.calculate_position_size(
            self.equity, len(tradable)
        )

        # Open position for each asset
        for asset_obj in tradable:
            asset_symbol = asset_obj.symbol
            ohlc = market_data.get_asset_ohlc(asset_symbol)
            if ohlc is None:
                continue

            entry_price = ohlc.open
            direction_int = self.regime_direction_map[regime.name]

            # Hard stop from config (risk.hard_stop_pct)
            stop_price = self.risk_manager.calculate_stop_price(entry_price, direction_int)

            # Create position
            position = Position(
                asset=asset_symbol,
                direction=direction_int,
                entry_price=entry_price,
                stop_price=stop_price,
                position_size=position_per_asset,
                leverage=self.position_sizer.leverage,
                entry_date=date,
                regime=regime.name
            )

            self.open_positions[asset_symbol] = position

            logger.info(f"    {asset_symbol} {'SHORT' if direction_int==-1 else 'LONG'} | "
                       f"Entry: {entry_price:.5f} | Stop: {stop_price:.5f} | "
                       f"Size: ${position_per_asset:,.0f} | "
                       f"Lev: {self.position_sizer.leverage}x")

        return trades

    def manage_positions(self, market_data, date: str) -> List[Trade]:
        """Manage open positions - check stops, exit at close"""
        closed_trades = []

        for asset_symbol, position in list(self.open_positions.items()):
            ohlc = market_data.get_asset_ohlc(asset_symbol)
            if ohlc is None:
                continue

            high = ohlc.high
            low = ohlc.low
            close = ohlc.close
            entry_price = position.entry_price
            stop_price = position.stop_price
            direction = position.direction

            # Check stop loss
            stop_hit = False
            exit_price = close
            exit_reason = ExitReason.CLOSE.value

            if self.config.risk.stop_loss_type != "none":
                if direction == Direction.SHORT.value:
                    if high >= stop_price:
                        stop_hit = True
                        exit_price = stop_price
                        exit_reason = ExitReason.STOP_LOSS.value
                else:
                    if low <= stop_price:
                        stop_hit = True
                        exit_price = stop_price
                        exit_reason = ExitReason.STOP_LOSS.value

            # Calculate PnL
            if direction == Direction.SHORT.value:
                pnl_pct = (entry_price - exit_price) / entry_price
            else:
                pnl_pct = (exit_price - entry_price) / entry_price

            notional = position.position_size * position.leverage
            pnl_usd = pnl_pct * notional

            # Create trade record
            trade = Trade(
                trade_id=f"{asset_symbol}-{date}-{exit_reason}",
                asset=asset_symbol,
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                stop_price=stop_price,
                entry_date=position.entry_date,
                exit_date=date,
                position_size=position.position_size,
                leverage=position.leverage,
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd,
                exit_reason=exit_reason,
                regime=position.regime,
                stop_hit=stop_hit
            )

            closed_trades.append(trade)
            del self.open_positions[asset_symbol]

            logger.info(f"    {asset_symbol} {'SHORT' if direction==-1 else 'LONG'} | "
                       f"Entry: {entry_price:.5f} | Exit: {exit_price:.5f} | "
                       f"Ret: {pnl_pct*100:+.2f}% | PnL: ${pnl_usd:+,.0f} | {exit_reason} | "
                       f"{'WIN' if pnl_usd > 0 else 'LOSS'}")

        return closed_trades

    def process_day(self, market_data, date: str) -> Tuple[List[Trade], float]:
        """Process a single trading day per the Agba Metta rules."""
        # Reset daily tracking
        self.risk_manager.reset_daily(self.equity)

        # Determine regime from the day's real yield
        real_yield = market_data.real_yield
        regime = self.determine_regime(real_yield)

        logger.info(f">>> {date} | Yield: {real_yield:.2f}% | Regime: {regime.name}")

        closed_trades = []

        # Manage existing positions
        if self.open_positions:
            closed = self.manage_positions(market_data, date)
            closed_trades.extend(closed)

        # Check for new trades (only if flat and not halted by a risk breaker)
        if not self.open_positions and not self.halted:
            alignment = self.alignment_filter.check_alignment(market_data, regime)
            is_trade_day = alignment.aligned and regime != Regime.STABILITY

            if is_trade_day:
                new_trades = self.open_positions_for_day(market_data, regime, date)
                # These will be closed at end of day
                if self.open_positions:
                    closed = self.manage_positions(market_data, date)
                    closed_trades.extend(closed)

        # Calculate daily PnL
        daily_pnl = sum(t.pnl_usd for t in closed_trades)
        self.equity += daily_pnl
        self.closed_trades.extend(closed_trades)  # Track closed trades

        # Record equity snapshot
        equity_snapshot = DailyEquity(
            date=date,
            equity=self.equity,
            daily_pnl=daily_pnl,
            daily_pnl_pct=(daily_pnl / (self.equity - daily_pnl)) * 100 if self.equity != daily_pnl else 0,
            regime=regime.name,
            trade_day=len(closed_trades) > 0,
            aligned=True,  # alignment.aligned if 'alignment' in locals() else False
            open_positions=len(self.open_positions)
        )
        self.equity_curve.append(equity_snapshot)

        # Update peak equity
        if self.equity > self.risk_manager.peak_equity:
            self.risk_manager.peak_equity = self.equity

        # Check risk limits. These actually halt the engine: previously they
        # only logged, so the configured max-drawdown and daily-loss circuit
        # breakers had no effect on the backtest at all.
        if self.risk_manager.check_max_drawdown(self.equity):
            logger.warning("  MAX DRAWDOWN EXCEEDED! Halting.")
            self.halted = True
            self.halt_reason = "MAX_DRAWDOWN"

        if self.risk_manager.check_daily_loss_limit(self.equity):
            logger.warning("  DAILY LOSS LIMIT EXCEEDED! Halting.")
            self.halted = True
            self.halt_reason = self.halt_reason or "DAILY_LOSS_LIMIT"

        return closed_trades, self.equity


def run_backtest(config: AgbaMettaConfig, market_data_dict: Dict[str, dict]) -> Tuple[List[Trade], pd.DataFrame, dict]:
    """Run complete backtest"""
    # Import here to avoid circular imports
    import pandas as pd

    engine = AgbaMettaEngine(config)

    # Convert market data dict to MarketData objects
    market_data_map = {}
    for date, data in market_data_dict.items():
        market_data_map[date] = MarketData(
            date=date,
            gold=OHLCData(**data['gold']),
            eur=OHLCData(**data['eur']),
            aud=OHLCData(**data['aud']),
            real_yield=data['real_yield']
        )

    # Run backtest
    dates = sorted(market_data_map.keys())

    for date in dates:
        if date < config.backtest.start_date or date > config.backtest.end_date:
            continue

        engine.process_day(market_data_map[date], date)

    # Calculate metrics
    metrics = calculate_metrics(engine.closed_trades, engine.equity_curve, config.backtest.initial_capital)

    return engine.closed_trades, engine.equity_curve, metrics


def calculate_metrics(trades: List[Trade], equity_curve: List[DailyEquity], initial_capital: float) -> dict:
    """Calculate performance metrics"""
    if not trades or not equity_curve:
        return {}

    equity_df = pd.DataFrame([e.to_dict() for e in equity_curve])
    final_equity = equity_df['equity'].iloc[-1]
    total_return = (final_equity / initial_capital - 1) * 100

    # Day-level win rate
    trade_days = [e for e in equity_curve if e.trade_day]
    day_wins = sum(1 for e in trade_days if e.daily_pnl > 0)
    day_total = len(trade_days)
    day_wr = day_wins / day_total * 100 if day_total > 0 else 0

    # Asset-level win rate
    asset_wins = sum(1 for t in trades if t.pnl_usd > 0)
    asset_total = len(trades)
    asset_wr = asset_wins / asset_total * 100 if asset_total > 0 else 0

    # Max drawdown
    peak = equity_df['equity'].expanding().max()
    dd = (equity_df['equity'] - peak) / peak
    max_dd = dd.min() * 100

    # Sharpe
    daily_rets = equity_df['equity'].pct_change().dropna()
    sharpe = daily_rets.mean() / (daily_rets.std() + 1e-9) * np.sqrt(252) if len(daily_rets) > 1 else 0

    # Profit factor
    gross_profit = sum(t.pnl_usd for t in trades if t.pnl_usd > 0)
    gross_loss = abs(sum(t.pnl_usd for t in trades if t.pnl_usd < 0))
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    return {
        "initial_capital": initial_capital,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return, 2),
        "trade_days": day_total,
        "day_wins": day_wins,
        "day_losses": day_total - day_wins,
        "day_win_rate_pct": round(day_wr, 2),
        "asset_trades": asset_total,
        "asset_wins": asset_wins,
        "asset_losses": asset_total - asset_wins,
        "asset_win_rate_pct": round(asset_wr, 2),
        "profit_factor": round(pf, 2) if pf != float('inf') else "inf",
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
    }


if __name__ == "__main__":
    # Quick test
    config = load_config()
    print(f"Loaded config: {config.model.name} v{config.model.version}")
    print(f"Assets: {[a.symbol for a in config.universe.assets]}")
    print(f"Risk per trade: {config.position_sizing.risk_per_trade_pct*100}%")
    print(f"Leverage: {config.position_sizing.leverage}x")
    print(f"Hard stop: {config.risk.hard_stop_pct*100}%")