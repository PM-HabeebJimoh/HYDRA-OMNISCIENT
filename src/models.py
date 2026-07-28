"""
Agba Metta Model - Core Data Structures
Standalone enums and data classes for the execution engine
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List
import json


class Regime(Enum):
    STABILITY = 0
    EXPANSION = 1
    CONTRACTION = 2

    @classmethod
    def from_yield(cls, yield_pct: float, contraction_thresh: float = 0.7, expansion_thresh: float = -0.1):
        if yield_pct > contraction_thresh:
            return cls.CONTRACTION
        elif yield_pct < expansion_thresh:
            return cls.EXPANSION
        return cls.STABILITY

    @property
    def direction(self) -> int:
        return {
            Regime.CONTRACTION: -1,  # SHORT
            Regime.EXPANSION: 1,     # LONG
            Regime.STABILITY: 0      # FLAT
        }[self]


class Direction(Enum):
    FLAT = 0
    LONG = 1
    SHORT = -1


class ExitReason(Enum):
    CLOSE = "CLOSE"
    STOP_LOSS = "STOP_LOSS"
    MAX_DD = "MAX_DD"
    REGIME_CHANGE = "REGIME_CHANGE"
    ALIGNMENT_LOST = "ALIGNMENT_LOST"


class SignalStatus(Enum):
    NO_SIGNAL = 0
    ALIGNED = 1
    MISALIGNED = 2


@dataclass
class OHLCData:
    """Real OHLC data from verified sources"""
    date: str
    open: float
    high: float
    low: float
    close: float
    
    def to_dict(self):
        return {
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            date=data["date"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"]
        )


@dataclass
class MarketData:
    """Complete market data for one day"""
    date: str
    gold: OHLCData
    eur: OHLCData
    aud: OHLCData
    real_yield: float
    
    def get_asset_ohlc(self, symbol: str) -> OHLCData:
        mapping = {"XAUUSD": self.gold, "EURUSD": self.eur, "AUDUSD": self.aud}
        return mapping.get(symbol)
    
    def get_all_ohlc(self) -> Dict[str, OHLCData]:
        return {"XAUUSD": self.gold, "EURUSD": self.eur, "AUDUSD": self.aud}


@dataclass
class Trade:
    """Completed trade record"""
    trade_id: str
    asset: str
    direction: int  # 1 = LONG, -1 = SHORT
    entry_price: float
    exit_price: float
    stop_price: float
    entry_date: str
    exit_date: str
    position_size: float
    leverage: int
    pnl_pct: float
    pnl_usd: float
    exit_reason: str
    regime: str
    stop_hit: bool = False
    equity_after: float = 0.0  # Equity after this trade closed
    
    def to_dict(self):
        return {
            "trade_id": self.trade_id,
            "asset": self.asset,
            "direction": "LONG" if self.direction == 1 else "SHORT",
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "stop_price": self.stop_price,
            "entry_date": self.entry_date,
            "exit_date": self.exit_date,
            "position_size": self.position_size,
            "leverage": self.leverage,
            "pnl_pct": round(self.pnl_pct * 100, 4),
            "pnl_usd": round(self.pnl_usd, 2),
            "exit_reason": self.exit_reason,
            "regime": self.regime,
            "stop_hit": self.stop_hit
        }


@dataclass
class DailyEquity:
    """Daily equity snapshot"""
    date: str
    equity: float
    daily_pnl: float
    daily_pnl_pct: float
    regime: str
    trade_day: bool
    aligned: bool
    open_positions: int
    
    def to_dict(self):
        return {
            "date": self.date,
            "equity": round(self.equity, 2),
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_pnl_pct": round(self.daily_pnl_pct, 4),
            "regime": self.regime,
            "trade_day": self.trade_day,
            "aligned": self.aligned,
            "open_positions": self.open_positions
        }


@dataclass
class Position:
    """Open position during trading"""
    asset: str
    direction: int  # 1 = LONG, -1 = SHORT
    entry_price: float
    stop_price: float
    position_size: float  # cash allocated
    leverage: int
    entry_date: str
    regime: str
    
    @property
    def notional(self) -> float:
        return self.position_size * self.leverage


class AlignmentResult:
    """Result of alignment check"""
    def __init__(self, aligned: bool, reason: str = ""):
        self.aligned = aligned
        self.reason = reason
    
    def __bool__(self):
        return self.aligned