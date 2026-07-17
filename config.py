import os

# ── Asset → OBI display label ─────────────────────────────────────────────────
# OBI is collected from Kraken BTC/USD (XBT/USD) L2 order book — a universal
# risk-sentiment proxy shared across all assets in each cycle.
# Binance (451) and Bybit (403) are geo-blocked from Replit servers.
SYMBOL_MAP = {
    'XAUUSD': 'XBTUSD',   # Kraken BTC/USD OBI proxy
    'XAGUSD': 'XBTUSD',   # Kraken BTC/USD OBI proxy
    'HG=F':   'XBTUSD',   # Kraken BTC/USD OBI proxy
    'EURUSD': 'XBTUSD',   # Kraken BTC/USD OBI proxy
    'AUDUSD': 'XBTUSD',   # Kraken BTC/USD OBI proxy
}

# ── API keys — sourced from environment only, never hardcoded ─────────────────
API_KEYS = {
    'nasa_firms': os.environ.get('NASA_FIRMS_KEY', ''),
    'eia':        os.environ.get('EIA_KEY', ''),
    'openaq':     os.environ.get('OPENAQ_KEY', ''),
    'etherscan':  os.environ.get('ETHERSCAN_KEY', ''),
}

# ── S3 Convergence Thresholds ─────────────────────────────────────────────────
# RealYield is the raw TIPS 10Y % (e.g., 1.85 for 1.85%).
# OBI is raw order book imbalance [-1, +1].
THRESHOLDS = {
    'CONTRACTION_YIELD': 0.7,    # TIPS yield > 0.7% → CONTRACTION regime
    'CONTRACTION_OBI':  -0.7,    # OBI ≤ -0.7 → confirmed SHORT in CONTRACTION
    'EXPANSION_YIELD':  -0.1,    # TIPS yield < -0.1% → EXPANSION regime
    'EXPANSION_OBI':     0.7,    # OBI ≥ +0.7 → confirmed LONG in EXPANSION
    'INEVITABLE_SCORE':  0.95,   # Score ≥ 0.95 → INEVITABLE
    'HARD_STOP_PCT':     0.01,   # 1% hard stop loss
}

# ── Monitored assets ──────────────────────────────────────────────────────────
MONITORED_ASSETS = ['XAUUSD', 'XAGUSD', 'HG=F', 'EURUSD', 'AUDUSD']

# ── Regime integer → name ─────────────────────────────────────────────────────
REGIMES = {
    0: "STABILITY",
    1: "EXPANSION",
    2: "CONTRACTION",
}
