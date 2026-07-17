"""
HYDRA-S3  |  S3-RHGNN Convergence Engine
Evaluates world state through the Recursive HyperGraph Neural Network.
Resilient to partial data — requires only RealYield + OBI for regime detection.

Score formula: smooth piecewise-linear across all three status zones.
  NOISE          → score 0.50 – 0.79   (|OBI| < 0.55)
  HIGH CONVICTION → score 0.80 – 0.94   (|OBI| 0.55 – 0.75)
  INEVITABLE     → score 0.95 – 0.999  (|OBI| > 0.75)
"""
import torch
import numpy as np
import logging
import math
from core.rhgnn_s3 import RecursiveHyperGraphS3, UniversalSignalManifoldS3
from config import THRESHOLDS, REGIMES

logger = logging.getLogger('HYDRA.S3Convergence')

# Piecewise linear score breakpoints: (|OBI|, score)
# Applies only when regime != STABILITY
_SCORE_BREAKS = [
    (0.00, 0.50),   # floor — no signal
    (0.30, 0.65),   # NOISE active
    (0.55, 0.80),   # HIGH CONVICTION entry
    (0.75, 0.95),   # INEVITABLE entry
    (0.95, 0.999),  # INEVITABLE peak
]


def _piecewise_score(obi_abs: float) -> float:
    """Map |OBI| → convergence score via smooth piecewise linear interpolation."""
    for i in range(len(_SCORE_BREAKS) - 1):
        x0, y0 = _SCORE_BREAKS[i]
        x1, y1 = _SCORE_BREAKS[i + 1]
        if obi_abs <= x1:
            t = (obi_abs - x0) / (x1 - x0) if x1 > x0 else 1.0
            return y0 + t * (y1 - y0)
    return _SCORE_BREAKS[-1][1]


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
        # else regime = 0  (STABILITY)

        # Direction aligns with OBI sign when signal is meaningful (|OBI| >= 0.30)
        if abs(obi_val) >= 0.30:
            direction = 1 if obi_val > 0 else -1

        # ── Score synthesis — smooth piecewise linear ──────────────────────
        # Score is regime-gated: STABILITY always returns 0.50 (NOISE)
        if regime != 0:
            score = _piecewise_score(abs(obi_val))
            # RHGNN latent energy micro-amplifier (capped at +2% to avoid inflation)
            lat_boost = min(abs(latent_sum) * 0.0002, 0.02)
            score = min(0.999, score + lat_boost)
        else:
            score = 0.50

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

        logger.debug(
            f"score={score:.4f} status={status} regime={REGIMES[regime]} "
            f"OBI={obi_val:+.4f} yield={yield_val:.3f}%"
        )

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
