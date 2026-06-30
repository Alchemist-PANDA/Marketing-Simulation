#!/usr/bin/env bash
set -e

echo "🚀 Starting FastAPI backend on port 8000..."
uvicorn api:app --host 0.0.0.0 --port 8000 &

echo "🚀 Starting Streamlit frontend on port 8501..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
