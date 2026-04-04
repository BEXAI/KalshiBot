#!/bin/bash
cd /Users/nathaniel/Kalshi

# Robust virtual environment injection
source .venv3.nosync/bin/activate 2>/dev/null || source venv.nosync/bin/activate 2>/dev/null

# Unbuffered execution prevents terminal hang and pushes exact strings instantly to the .log tracker
export PYTHONUNBUFFERED=1

# Pre-Flight Diagnostic Check
python3 audit_bot.py
if [ $? -ne 0 ]; then
    echo "[!] CRITICAL: Pre-flight Audit failed. Halting daemon."
    exit 1
fi

# Endpoint Parity Diagnostic Check
python3 src/utils/endpoint_health.py
if [ $? -ne 0 ]; then
    echo "[!] CRITICAL: Live API Schema execution structurally dropped. Halting daemon."
    exit 1
fi

# 'exec' replaces the overarching bash script PID with the raw Python PID ensuring launchd kills/restarts act beautifully
exec python3 main.py
