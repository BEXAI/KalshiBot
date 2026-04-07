#!/usr/bin/env bash
set -e

# Start FastAPI Background
echo "[BEXAI] Starting FastAPI Backend on :8000"
uvicorn dashboard_api:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Start Vite Frontend
echo "[BEXAI] Starting Vite React Frontend on :5173"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "[BEXAI] Full-Stack Kalshi Monitor Running!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both."

# Catch Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; echo '\n[BEXAI] Shutting down full stack...'" SIGINT SIGTERM

wait
