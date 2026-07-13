import asyncio
import logging
import json
import os
from datetime import datetime
from core.collector import S3CausalCollector
from core.convergence import S3ConvergenceEngine
from config import MONITORED_ASSETS, THRESHOLDS, SYMBOL_MAP

# Setup high-conviction logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_audit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HYDRA-S3-DAEMON')

STATE_FILE = "enterprise_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "equity": 100000.0,
        "initial_capital": 100000.0,
        "trades": [],
        "opportunities": [], # Now entries will include 'asset'
        "history": {asset: [] for asset in MONITORED_ASSETS}, # Per-asset history
        "settings": THRESHOLDS,
        "api_health": {k: "Unknown" for k in ["NASA", "EIA", "OpenAQ", "ETH", "RealYield", "OBI"]}
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

async def live_daemon():
    logger.info("🔱 HYDRA-S3 ENTERPRISE DAEMON: ACTIVATING 24/7 MULTI-ASSET MONITORING")
    
    engine = S3ConvergenceEngine()
    state = load_state()
    
    # Ensure history is initialized for all monitored assets
    for asset in MONITORED_ASSETS:
        if asset not in state['history']:
            state['history'][asset] = []
    
    cycle = 0
    try:
        while True:
            cycle += 1
            async with S3CausalCollector() as collector:
                # We fetch the common causal signals once per cycle to be efficient
                # But OBI is asset-specific.
                
                for asset in MONITORED_ASSETS:
                    binance_symbol = SYMBOL_MAP.get(asset, "PAXGUSDT")
                    
                    # Fetch the manifold specifically for this asset's OBI
                    world_state = await collector.collect_all_parallel(obi_symbol=binance_symbol)
                    report = engine.evaluate(world_state)
                    
                    score = report['score']
                    status = report['status']
                    regime = report['regime_name']
                    direction = report['direction']
                    
                    # 1. Update Per-Asset History
                    state['history'][asset].append({
                        "time": datetime.utcnow().isoformat(),
                        "score": score,
                        "status": status,
                        "regime": regime
                    })
                    
                    # 2. Update API Health (using the last asset's result for simplicity)
                    for k, v in world_state.items():
                        state['api_health'][k] = "ONLINE" if v is not None else "GAP"

                    # 3. OPPORTUNITY DETECTION LOGIC (Asset-Specific)
                    if score >= 0.7:
                        opp_id = f"{asset}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        opportunity = {
                            "id": opp_id,
                            "asset": asset,
                            "timestamp": datetime.utcnow().isoformat(),
                            "score": score,
                            "status": status,
                            "regime": regime,
                            "direction": direction,
                            "manifold_snapshot": world_state,
                            "executed": False,
                            "trade_id": None
                        }
                        
                        # Prevent duplicate rapid-fire opportunities for the same asset
                        asset_opps = [o for o in state['opportunities'] if o['asset'] == asset]
                        if not asset_opps or \
                           (datetime.utcnow().timestamp() - datetime.fromisoformat(asset_opps[-1]['timestamp']).timestamp() > 60):
                            
                            state['opportunities'].append(opportunity)
                            logger.info(f"🔥 OPPORTUNITY [{asset}]: {opp_id} | Score: {score:.4f} | Regime: {regime}")
                            
                            if status == "INEVITABLE":
                                logger.warning(f"🚨 S-ALERT: {asset} CONVERGENCE INEVITABLE | {opp_id}")

                    # Limit history size per asset
                    if len(state['history'][asset]) > 10000:
                        state['history'][asset] = state['history'][asset][-10000:]
                
                # Persistence: Save state after all assets are processed
                save_state(state)
                
            if cycle % 60 == 0:
                logger.info(f"System Heartbeat: {cycle} cycles completed. Monitoring {len(MONITORED_ASSETS)} assets 24/7.")
                
            await asyncio.sleep(10) # High-frequency causal polling
            
    except asyncio.CancelledError:
        logger.info("Daemon received cancellation signal.")
    except Exception as e:
        logger.critical(f"DAEMON CRITICAL FAILURE: {e}", exc_info=True)
        save_state(state)

if __name__ == "__main__":
    try:
        asyncio.run(live_daemon())
    except KeyboardInterrupt:
        pass
