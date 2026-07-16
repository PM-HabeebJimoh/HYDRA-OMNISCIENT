"""
HYDRA-S3  |  S3-RHGNN Convergence Engine
Evaluates world state through the Recursive HyperGraph Neural Network.
Resilient to partial data — requires only RealYield + OBI for regime detection.
"""
import torch
import numpy as np
import logging
import math
from core.rhgnn_s3 import RecursiveHyperGraphS3, UniversalSignalManifoldS3
from config import THRESHOLDS, REGIMES

logger = logging.getLogger('HYDRA.S3Convergence')


class S3ConvergenceEngine:
    def __init__(self, weights_path: str = 's3_weights.pth'):
        self.manifold = UniversalSignalManifoldS3(n_sources=100)
        self.model    = RecursiveHyperGraphS3(input_dim=100)
        self.weights_loaded = self.load_weights(weights_path)

    def load_weights(self, path: str) -> bool:
        try:
            weights = torch.load(path, map_location='cpu', weights_only=False)
            self.model.load_state_dict(weights['model_state_dict'])
            self.manifold.load_state_dict(weights['manifold_state_dict'])
            self.model.eval()
            self.manifold.eval()
            logger.info("✅ S3 Weights Loaded — S3-RHGNN v4.0 ONLINE")
            return True
        except Exception as e:
            logger.error(f"❌ Weight Load Failure: {e}. Running with random weights.")
            return False

    def evaluate(self, world_state: dict) -> dict:
        """
        Evaluate the causal manifold and produce a convergence report.

        Regime detection requires: RealYield (raw %) + OBI (raw -1..1).
        Neural inference uses all available non-None signals.
        Returns DATA_GAP only if both critical signals are absent.
        """
        yield_val = world_state.get('RealYield')
        obi_val   = world_state.get('OBI')

        # ── Fail closed only when BOTH critical signals are missing ──────────
        if yield_val is None and obi_val is None:
            logger.warning("Both RealYield and OBI unavailable → DATA_GAP")
            return self._data_gap(world_state)

        # Use last-known defaults if one is missing
        if yield_val is None:
            yield_val = 1.0   # neutral-ish real yield
            logger.warning("RealYield missing — using neutral default 1.0%")
        if obi_val is None:
            obi_val = 0.0
            logger.warning("OBI missing — using neutral default 0.0")

        # ── Neural inference (uses all available signals) ────────────────────
        latent_sum = 0.0
        try:
            # Build inference dict substituting None → 0.0 for the model
            infer_state = {k: (v if v is not None else 0.0)
                           for k, v in world_state.items()}

            with torch.no_grad():
                manifold_out = self.manifold.project(infer_state)      # (1, 100)
                hidden_dim   = self.model.hidden_dim
                adj          = torch.eye(hidden_dim)                    # (256, 256)
                convergence_out, direction_out, regime_out, h = \
                    self.model(manifold_out, adj)
                latent_sum = torch.sum(h).item()

            if not math.isfinite(latent_sum):
                logger.warning(f"Non-finite latent sum ({latent_sum}) — clamping to 0")
                latent_sum = 0.0

        except Exception as e:
            logger.error(f"Neural inference error: {e}")
            latent_sum = 0.0

        # ── Rule-based regime classification ─────────────────────────────────
        regime    = 0
        direction = 0

        if yield_val > THRESHOLDS['CONTRACTION_YIELD']:
            regime = 2   # CONTRACTION
        elif yield_val <= THRESHOLDS['EXPANSION_YIELD']:
            regime = 1   # EXPANSION

        # Direction: based on OBI magnitude so it aligns with the score display.
        # Score rises when |OBI| >= 0.5 — direction must match so BIAS is never
        # NEUTRAL while the score shows a live signal.
        OBI_STRONG = 0.5   # matches score's lower-tier threshold
        if abs(obi_val) >= OBI_STRONG:
            direction = 1 if obi_val > 0 else -1

        # ── Score synthesis ────────────────────────────────────────────────
        # Score rises when: regime ≠ STABILITY AND OBI confirms direction
        # Latent energy from the RHGNN amplifies marginally
        score = 0.5
        if regime != 0 and abs(obi_val) >= 0.7:
            base  = 0.96
            obi_c = abs(obi_val) * 0.04      # 0.028..0.04 for |OBI| 0.7..1
            lat_c = min(abs(latent_sum) * 0.0005, 0.02)  # capped contribution
            score = min(0.999, base + obi_c + lat_c)
        elif regime != 0 and abs(obi_val) >= 0.5:
            score = 0.5 + abs(obi_val) * 0.3   # 0.65..0.80 range

        if not math.isfinite(score):
            score = 0.0

        # ── Status classification ─────────────────────────────────────────
        inev_threshold = THRESHOLDS.get('INEVITABLE_SCORE', 0.95)
        if score >= inev_threshold:
            status = "INEVITABLE"
        elif score >= 0.80:
            status = "HIGH CONVICTION"
        else:
            status = "NOISE"

        return {
            'score':          score,
            'status':         status,
            'direction':      direction,
            'regime':         regime,
            'regime_name':    REGIMES[regime],
            'world_state':    world_state,
            'latent_sum':     latent_sum,
            'yield_raw':      yield_val,
            'obi_raw':        obi_val,
        }

    @staticmethod
    def _data_gap(world_state: dict) -> dict:
        return {
            'score':       0.0,
            'status':      'DATA_GAP',
            'direction':   0,
            'regime':      0,
            'regime_name': REGIMES[0],
            'world_state': world_state,
            'latent_sum':  0.0,
            'yield_raw':   None,
            'obi_raw':     None,
        }
