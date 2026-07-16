#!/bin/bash
# HYDRA-S3 Enterprise OS — Deployment Startup
# Starts the live daemon in background, then serves Streamlit (foreground)
echo "╔══════════════════════════════════════════╗"
echo "║   HYDRA-S3 ENTERPRISE OS — STARTUP       ║"
echo "╚══════════════════════════════════════════╝"

echo "[1/2] Launching 24/7 Live Daemon..."
python live_engine.py >> system_audit.log 2>&1 &
DAEMON_PID=$!
echo "  Daemon PID: $DAEMON_PID"

echo "[2/2] Starting Streamlit Terminal..."
exec streamlit run app.py \
    --server.port=5000 \
    --server.address=0.0.0.0 \
    --server.headless=true
