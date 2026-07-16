#!/bin/bash
set -e
echo "╔══════════════════════════════════════╗"
echo "║  HYDRA-S3 ENTERPRISE BUILD PIPELINE  ║"
echo "╚══════════════════════════════════════╝"

echo "[1/3] Installing PyTorch CPU (numpy-2.x compatible)..."
pip install --quiet torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu

echo "[2/3] Installing core dependencies..."
pip install --quiet -r requirements.txt

echo "[3/3] Verifying critical imports..."
python3 -c "import torch, numpy; print(f'  torch {torch.__version__}  numpy {numpy.__version__}  OK')"

echo "Build complete ✓"
