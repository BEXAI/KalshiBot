#!/bin/bash
cd /Users/nathaniel/Kalshi

# Robust virtual environment injection
source .venv3.nosync/bin/activate 2>/dev/null || source venv.nosync/bin/activate 2>/dev/null

# Unbuffered execution prevents terminal hang and pushes exact strings instantly to the .log tracker
export PYTHONUNBUFFERED=1

# 'exec' replaces the overarching bash script PID with the raw Python PID ensuring launchd kills/restarts act beautifully
exec /Users/nathaniel/Kalshi/.venv3.nosync/bin/python main.py
