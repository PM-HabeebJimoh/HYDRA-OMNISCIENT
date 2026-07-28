"""
Agba Metta Model - Configuration Loader
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    name: str
    version: str
    description: str


@dataclass
class AssetConfig:
    symbol: str
    name: str
    contract_size: int
    tick_size: float


@dataclass
class UniverseConfig:
    assets: List[AssetConfig]

    def __post_init__(self):
        # Convert dict assets to AssetConfig objects if needed
        converted = []
        for a in self.assets:
            if isinstance(a, dict):
                converted.append(AssetConfig(**a))
            else:
                converted.append(a)
        self.assets = converted


@dataclass
class RegimeConfig:
    contraction_yield_threshold: float
    expansion_yield_threshold: float


@dataclass
class AlignmentConfig:
    enabled: bool
    contraction_requires_all_down: bool
    expansion_requires_all_up: bool


@dataclass
class PositionSizingConfig:
    risk_per_trade_pct: float
    leverage: int
    equal_weight: bool
    max_assets_per_trade: int


@dataclass
class RiskConfig:
    hard_stop_pct: float
    max_drawdown_pct: float
    max_daily_loss_pct: float
    stop_loss_type: str


@dataclass
class ExecutionConfig:
    entry: str
    exit: str
    stop_check: str
    stop_behavior: str
    allow_reentry_same_day: bool


@dataclass
class RegimeDirectionConfig:
    CONTRACTION: int
    EXPANSION: int
    STABILITY: int


@dataclass
class BacktestConfig:
    start_date: str
    end_date: str
    initial_capital: float
    commission_per_trade: float
    slippage_pct: float


@dataclass
class AgbaMettaConfig:
    model: ModelConfig
    universe: UniverseConfig
    regime: RegimeConfig
    alignment: AlignmentConfig
    position_sizing: PositionSizingConfig
    risk: RiskConfig
    execution: ExecutionConfig
    regime_direction: RegimeDirectionConfig
    backtest: BacktestConfig

    @classmethod
    def from_yaml(cls, path: str) -> 'AgbaMettaConfig':
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            model=ModelConfig(**data.get('model', {})),
            universe=UniverseConfig(**data.get('universe', {})),
            regime=RegimeConfig(**data.get('regime', {})),
            alignment=AlignmentConfig(**data.get('alignment', {})),
            position_sizing=PositionSizingConfig(**data.get('position_sizing', {})),
            risk=RiskConfig(**data.get('risk', {})),
            execution=ExecutionConfig(**data.get('execution', {})),
            regime_direction=RegimeDirectionConfig(**data.get('regime_direction', {})),
            backtest=BacktestConfig(**data.get('backtest', {}))
        )


def load_config(config_path: str = None) -> AgbaMettaConfig:
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "model_config.yaml"
    return AgbaMettaConfig.from_yaml(str(config_path))