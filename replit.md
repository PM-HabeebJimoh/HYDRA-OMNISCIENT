# HYDRA-OMNISCIENT (HYDRA-S3)

## Project Overview
Enterprise-grade quantitative trading terminal built on the **S3-RHGNN v4.0** model (Recursive HyperGraph Neural Network). Monitors 5 global assets (XAUUSD, XAGUSD, HG=F, EURUSD, AUDUSD) in real-time using a multi-signal causal convergence engine.

## Stack
- **Frontend/UI**: Streamlit (Bloomberg/Reuters terminal style)
- **ML Model**: PyTorch — RecursiveHyperGraphS3 + UniversalSignalManifoldS3
- **Data Collection**: aiohttp (async) — NASA FIRMS, EIA Energy, OpenAQ, Etherscan, FRED, Binance OBI
- **Visualization**: Plotly

## How to Run
The Streamlit UI is the main web application:
```
streamlit run app.py
```
Runs on port 5000.

The live data daemon (runs separately, feeds `enterprise_state.json`):
```
python live_engine.py
```

## Architecture
- `app.py` — Streamlit web app (5 modules: Matrix Dashboard, Opportunity Hub, Trade Audit Ledger, Surgical Causal Lab, System Configuration)
- `live_engine.py` — Background daemon polling APIs every 10 seconds, writing to `enterprise_state.json`
- `core/convergence.py` — S3ConvergenceEngine: loads PyTorch weights, evaluates world state
- `core/rhgnn_s3.py` — RecursiveHyperGraphS3 + UniversalSignalManifoldS3 model definition
- `core/collector.py` — Async causal data collector (6 external APIs)
- `core/allocator.py` — Anti-fragile position allocator
- `config.py` — API keys, thresholds, asset list, regime mapping
- `s3_weights.pth` — Pre-trained PyTorch model weights

## State Persistence
State is saved to `enterprise_state.json` (auto-created on first run, persists across restarts).

## User Preferences
- Deploy exactly as imported — no restructuring or migrations
