#!/usr/bin/env bash
set -euo pipefail

echo "=== HYDRA-S3 Production Build ==="

# Install CPU-only PyTorch first (~200 MB vs 1.2 GB for CUDA build)
echo "[1/2] Installing PyTorch (CPU-only)..."
pip install --quiet \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.2+cpu

# Install remaining dependencies
echo "[2/2] Installing application dependencies..."
pip install --quiet -r requirements.txt

echo "=== Build complete ==="
