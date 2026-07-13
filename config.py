# Asset to Binance Symbol Mapping
# This ensures the S3 OBI signal is pulled for the correct asset
SYMBOL_MAP = {
    'XAUUSD': 'PAXGUSDT',
    'XAGUSD': 'XAGUSDT', # Note: Liquidity varies by exchange
    'HG=F': 'COPPERUSDT', # Proxy
    'EURUSD': 'EURUSDT',
    'AUDUSD': 'AUDUSDT'
}

API_KEYS = {
    'nasa_firms': '87a49964d715930ff463e734dfde2ff6',
    'eia': 'Mf8KoXCW4x8B61Bhe6qnjTkUqf1hrMj9hIfrvRHc',
    'openaq': 'b3ec85742e441854b043c6ab1d391c3b6981b000dc4c902f15e95ebd066e66c3',
    'etherscan': 'ASQM5BAMNEPYQNRBDZ671QPUXSGKVUMPTX',
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
