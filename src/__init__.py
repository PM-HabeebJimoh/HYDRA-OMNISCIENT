"""
Agba Metta Model - Package init
"""

from src.models import (
    OHLCData, MarketData, Trade, DailyEquity, Position,
    Regime, Direction, ExitReason, AlignmentResult
)
from src.config_loader import AgbaMettaConfig, load_config
from src.engine import AgbaMettaEngine, run_backtest, calculate_metrics

__all__ = [
    'OHLCData', 'MarketData', 'Trade', 'DailyEquity', 'Position',
    'Regime', 'Direction', 'ExitReason', 'AlignmentResult',
    'AgbaMettaConfig', 'load_config',
    'AgbaMettaEngine', 'run_backtest', 'calculate_metrics'
]

__version__ = "1.0.0"
__author__ = "Agba Metta Team"