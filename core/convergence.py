import torch
import numpy as np
import logging
import math
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
            weights = torch.load(path, map_location='cpu', weights_only=False)
            self.model.load_state_dict(weights['model_state_dict'])
            self.manifold.load_state_dict(weights['manifold_state_dict'])
            logger.info("✅ S3 Weights Loaded Successfully.")
        except Exception as e:
            logger.error(f"❌ Weight Load Failure: {e}. Running with random weights.")

    def evaluate(self, world_state: dict) -> dict:
        # Fail closed when any signal is missing
        if any(v is None for v in world_state.values()):
            return {
                'status': 'DATA_GAP',
                'score': 0.0,
                'regime': 0,
                'regime_name': REGIMES[0],
                'direction': 0
            }

        try:
            with torch.no_grad():
                # Project the world_state dict through the manifold
                manifold_out = self.manifold.project(world_state)  # shape: (1, 100)

                # Build a fixed identity adjacency matrix for the graph layers
                hidden_dim = self.model.hidden_dim
                adj = torch.eye(hidden_dim)  # (256, 256)

                # Forward pass: returns (convergence, direction, regime_probs, h)
                convergence_out, direction_out, regime_out, h = self.model(manifold_out, adj)
                state_sum = torch.sum(h).item()

            # NaN / Inf guard — fail closed rather than propagate invalid scores
            if not math.isfinite(state_sum):
                logger.warning(f"⚠️ Non-finite latent sum ({state_sum}); returning DATA_GAP.")
                return {
                    'status': 'DATA_GAP',
                    'score': 0.0,
                    'regime': 0,
                    'regime_name': REGIMES[0],
                    'direction': 0
                }

        except Exception as e:
            logger.error(f"❌ Inference error: {e}")
            return {
                'status': 'DATA_GAP',
                'score': 0.0,
                'regime': 0,
                'regime_name': REGIMES[0],
                'direction': 0
            }

        yield_val = world_state.get('RealYield', 0) or 0
        obi = world_state.get('OBI', 0) or 0
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

        # Final NaN guard on score itself
        if not math.isfinite(score):
            score = 0.0

        status = "INEVITABLE" if score >= THRESHOLDS['INEVITABLE_SCORE'] else \
                 "HIGH CONVICTION" if score >= 0.80 else "NOISE"

        return {
            'score': score, 'status': status, 'direction': direction,
            'regime': regime, 'regime_name': REGIMES[regime],
            'world_state': world_state, 'latent_sum': state_sum
        }
