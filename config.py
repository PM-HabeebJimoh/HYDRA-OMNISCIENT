import os

# Asset to Binance Symbol Mapping
# This ensures the S3 OBI signal is pulled for the correct asset
SYMBOL_MAP = {
    'XAUUSD': 'PAXGUSDT',
    'XAGUSD': 'XAGUSDT', # Note: Liquidity varies by exchange
    'HG=F': 'COPPERUSDT', # Proxy
    'EURUSD': 'EURUSDT',
    'AUDUSD': 'AUDUSDT'
}

# API keys loaded from environment — never hardcode credentials in source.
# Set these as Replit Secrets: NASA_FIRMS_KEY, EIA_KEY, OPENAQ_KEY, ETHERSCAN_KEY
API_KEYS = {
    'nasa_firms': os.environ.get('NASA_FIRMS_KEY', ''),
    'eia': os.environ.get('EIA_KEY', ''),
    'openaq': os.environ.get('OPENAQ_KEY', ''),
    'etherscan': os.environ.get('ETHERSCAN_KEY', ''),
}

# S3 Convergence Thresholds (Surgical Truth)
THRESHOLDS = {
    'CONTRACTION_YIELD': 0.7,
    'CONTRACTION_OBI': -0.7,
    'EXPANSION_YIELD': -0.1,
    'EXPANSION_OBI': 0.7,
    'INEVITABLE_SCORE': 0.95,
    'HARD_STOP_PCT': 0.01, # 1%
}

# Assets Monitored
MONITORED_ASSETS = ['XAUUSD', 'XAGUSD', 'HG=F', 'EURUSD', 'AUDUSD']

# Regime Mapping
REGIMES = {
    0: "STABILITY",
    1: "EXPANSION",
    2: "CONTRACTION"
}
