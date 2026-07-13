---
name: Deployment config
description: Production deployment settings for HYDRA-S3 Streamlit terminal
---

# Deployment Config — HYDRA-S3

**Target:** autoscale (stateless Streamlit UI; daemon runs separately)

**Run command:** `["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]`

**Why:** autoscale is correct for the Streamlit UI alone. The live_engine.py daemon is a separate concern (Task #2, now cancelled). Streamlit is stateless per-request; shared state goes through enterprise_state.json.

**Note:** Deployment was not previously configured (no [deployment] section in .replit). deployConfig() call added it successfully.
