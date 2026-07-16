import os

# ── Asset → Binance symbol mapping for OBI signal ─────────────────────────────
# Uses Binance Futures (fapi) symbols where available (deeper liquidity).
# collector.py tries fapi first, then spot.
SYMBOL_MAP = {
    'XAUUSD': 'XAUUSDT',   # Gold/USDT perpetual futures (fapi)
    'XAGUSD': 'ETHUSDT',   # Silver proxy via ETH (best available liquid proxy)
    'HG=F':   'ETHUSDT',   # Copper proxy via ETH
    'EURUSD': 'EURUSDT',   # EUR/USDT spot (Binance)
    'AUDUSD': 'AUDUSDT',   # AUD/USDT spot (Binance)
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
