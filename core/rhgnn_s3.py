import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np

class RecursiveHyperGraphS3(nn.Module):
    """
    HYDRA-SINGULARITY S3: The Regime-Symmetry Break Engine.
    
    Implements the Symmetry-Break Layer to detect regime flips 
    and the Zero-Lag Manifold for instantaneous reaction.
    """
    def __init__(self, input_dim: int = 100, hidden_dim: int = 256, layers: int = 4):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        self.projection = nn.Linear(input_dim, hidden_dim)
        self.norm_proj = nn.LayerNorm(hidden_dim)
        
        self.graph_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim) for _ in range(layers)
        ])
        
        self.norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(layers)
        ])
        
        self.reaction_loop = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh()
        )
        
        # Convergence Head
        self.convergence_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        # Directional Head
        self.direction_head = nn.Linear(hidden_dim, 1)
        
        # REGIME SYMMETRY-BREAK LAYER
        # Predicts: 0: Stability, 1: Expansion, 2: Contraction
        self.regime_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 3),
            nn.Softmax(dim=-1)
        )

    def forward(self, x: torch.Tensor, adjacency_matrix: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.projection(x)
        h = self.norm_proj(h)
        
        for i, layer in enumerate(self.graph_layers):
            agg = torch.matmul(h, adjacency_matrix) 
            h = F.relu(layer(h + agg))
            h = self.norms[i](h)
            reaction = self.reaction_loop(h)
            h = h + reaction
            
        convergence = self.convergence_head(h)
        
        direction = torch.tanh(self.direction_head(h))
        regime = self.regime_head(h)
        
        return convergence, direction, regime, h

class UniversalSignalManifoldS3(nn.Module):
    """
    Zero-Lag Manifold Projection.
    Optimized for instantaneous causal coordinate mapping.
    """
    def __init__(self, n_sources: int = 100):
        super().__init__()
        self.n_sources = n_sources
        self.manifold_proj = nn.Linear(n_sources, 100)
        
    def project(self, signal_dict: Dict) -> torch.Tensor:
        # Extract values from the dict based on keys present, otherwise 0.0
        # To keep it consistent with n_sources, we use a fixed list of expected keys 
        # or just iterate through the dict and pad.
        vec = []
        # We'll use the keys present in the dict and pad the rest.
        # For training, we want a consistent ordering.
        sorted_keys = sorted(signal_dict.keys())
        for k in sorted_keys:
            vec.append(float(signal_dict[k]))
            
        # Pad to n_sources
        while len(vec) < self.n_sources:
            vec.append(0.0)
        
        # Truncate if too many
        vec = vec[:self.n_sources]
            
        tensor = torch.tensor(vec, dtype=torch.float32).unsqueeze(0)
        return self.manifold_proj(tensor)
