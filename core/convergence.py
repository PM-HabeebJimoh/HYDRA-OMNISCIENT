import torch
import numpy as np
import logging
from core.rhgnn_s3 import RecursiveHyperGraphS3, UniversalSignalManifoldS3
from config import THRESHOLDS, REGIMES

logger = logging.getLogger('HYDRA.S3Convergence')

class S3ConvergenceEngine:
    def __init__(self, weights_path='s3_weights.pth'):
        self.manifold = UniversalSignalManifoldS3(n_sources=100)
        self.model = RecursiveHyperGraphS3(input_dim=100)
        self.load_weights(weights_path)

    def load_weights(self, path):
        try:
            weights = torch.load(path)
            self.model.load_state_dict(weights['model_state_dict'])
            self.manifold.load_state_dict(weights['manifold_state_dict'])
            logger.info("✅ S3 Weights Loaded Successfully.")
        except Exception as e:
            logger.error(f"❌ Weight Load Failure: {e}")

    def evaluate(self, world_state: dict) -> dict:
        if any(v is None for v in world_state.values()):
            return {
                'status': 'DATA_GAP', 
                'score': 0.0, 
                'regime': 0, 
                'regime_name': REGIMES[0],
                'direction': 0
            }

        raw_tensor = torch.zeros((1, 100))
        vals = list(world_state.values())
        for i in range(min(len(vals), 100)):
            raw_tensor[0, i] = vals[i]
            
        with torch.no_grad():
            manifold_state = self.manifold.project(raw_tensor)
            latent = self.model(manifold_state)
            state_sum = torch.sum(latent).item()

        yield_val = world_state.get('RealYield', 0)
        obi = world_state.get('OBI', 0)
        regime = 0 
        direction = 0
        
        if yield_val > THRESHOLDS['CONTRACTION_YIELD']: 
            regime = 2 
            direction = -1 if obi <= THRESHOLDS['CONTRACTION_OBI'] else 0
        elif yield_val <= THRESHOLDS['EXPANSION_YIELD']:
            regime = 1 
            direction = 1 if obi >= THRESHOLDS['EXPANSION_OBI'] else 0
            
        score = 0.5
        if regime != 0 and abs(obi) >= 0.7:
            score = min(0.999, 0.96 + (abs(obi) * 0.04) + (abs(state_sum) * 0.001))
            
        status = "INEVITABLE" if score >= THRESHOLDS['INEVITABLE_SCORE'] else "NOISE"
        
        return {
            'score': score, 'status': status, 'direction': direction,
            'regime': regime, 'regime_name': REGIMES[regime],
            'world_state': world_state, 'latent_sum': state_sum
        }
