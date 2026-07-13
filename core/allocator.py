import logging
from datetime import datetime
from config import THRESHOLDS

logger = logging.getLogger('HYDRA.S3Allocator')

class S3AntiFragileAllocator:
    def __init__(self, initial_capital: float = 10000.0):
        self.equity = initial_capital
        self.initial_capital = initial_capital
        self.open_positions = {}

    def calculate_leverage(self, score: float, regime: int) -> float:
        if score >= 0.95: leverage = 100.0
        elif score >= 0.80: leverage = 50.0
        else: leverage = 0.0
        if regime == 2: leverage *= 1.5
        return leverage

    def execute_trade(self, inst: str, direction: int, score: float, regime: int, price: float):
        if direction == 0: return None
        leverage = self.calculate_leverage(score, regime)
        if leverage == 0: return None
        amount_to_risk = self.equity * 0.02
        position_size = (amount_to_risk * leverage) / price
        sl_pct = THRESHOLDS['HARD_STOP_PCT']
        tp_pct = 0.20 if score >= 0.95 else 0.10
        trade = {
            'instrument': inst, 'direction': direction, 'entry_price': price,
            'size': abs(position_size), 'sl_price': price * (1 - sl_pct) if direction == 1 else price * (1 + sl_pct),
            'tp_price': price * (1 + tp_pct) if direction == 1 else price * (1 - tp_pct),
            'timestamp': datetime.utcnow()
        }
        self.open_positions[inst] = trade
        return trade

    def resolve_trade(self, inst: str, exit_price: float):
        if inst not in self.open_positions: return 0.0
        trade = self.open_positions.pop(inst)
        pnl = (exit_price - trade['entry_price']) * trade['size'] * trade['direction']
        self.equity += pnl
        return pnl
