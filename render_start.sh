#!/usr/bin/env bash
# Render startup for the Streamlit dashboard.
# Streamlit is launched with headless mode on $PORT (set by Render).

set -e

PORT="${PORT:-8501}"

streamlit run dashboard/app.py \
  --server.port "${PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false