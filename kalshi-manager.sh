#!/bin/bash
# ==============================================================================
# KalshiBot Native Environment Manager (kalshi-manager.sh)
# Master control script for deploying, managing, and tracking the KalshiBot daemon, 
# Claude Code environments, and natively scaffolding quantitative strategies.
# ==============================================================================

# Fast-fail heavily restricted architecture
set -e

# Target Absolute Directory Structuring
cd /Users/nathaniel/Kalshi

show_help() {
    echo "🤖 BEXAI / KalshiBot Autonomous Manager"
    echo "Usage: ./kalshi-manager.sh <command>"
    echo ""
    echo "Commands:"
    echo "  setup       - Configure Python .venv, dependencies, and Claude Code boundaries"
    echo "  vibe        - Boot a context-aware Claude native terminal coding session"
    echo "  launch      - Start the production KalshiBot daemon securely in the background"
    echo "  stop        - Safely terminate and kill all background daemon execution loops"
    echo "  dashboard   - Spin up the Streamlit interface (mapped naturally to the iPad UI)"
    echo "  scaffold    - Natively injects a new python quant strategy in src/strategies/"
    echo ""
}

setup() {
    echo ">> [SETUP] Establishing baseline environments natively..."
    if [ ! -d ".venv3.nosync" ]; then
        python3 -m venv .venv3.nosync
    fi
    source .venv3.nosync/bin/activate
    pip install -r requirements.txt || pip install aiohttp ecdsa cryptography torch numpy timesfm streamlit pandas altair
    echo ">> [SETUP] Environment configured seamlessly!"
}

vibe() {
    echo ">> [VIBE] Injecting CLAUDE.md context safely into Anthropic Vibe Coding Mode..."
    if command -v claude &> /dev/null; then
        claude
    else
        echo "[!] Claude CLI not detected globally. Run standard npm/brew installation routines!"
    fi
}

launch() {
    echo ">> [PRODUCTION] Deploying Master Daemon autonomously into the background..."
    bash start_daemon.sh &
    echo ">> [PRODUCTION] Locked. Use 'tail -f kalshi_trades.jsonlines' to monitor tracking."
}

stop() {
    echo ">> [STOP] Safely spinning down active LLM Queues and WebSocket listeners..."
    pkill -f "python3 main.py" || echo "No active daemon located natively."
    echo ">> [STOP] Completely terminated securely!"
}

dashboard() {
    echo ">> [UI] Broadcasing local dashboard onto Streamlit pipeline dynamically..."
    source .venv3.nosync/bin/activate 2>/dev/null || true
    streamlit run ipad_dashboard.py --server.address 0.0.0.0 --server.port 8501 &
}

scaffold() {
    if [ -z "$2" ]; then
        echo "[!] Provide a strategy filename natively: ./kalshi-manager.sh scaffold <name>"
        exit 1
    fi
    STRAT_FILE="src/strategies/$2.py"
    echo ">> [SCAFFOLD] Generating baseline quant logic natively in ${STRAT_FILE}..."
    cat << EOF > ${STRAT_FILE}
import asyncio
import time

class ${2^}QuantitativeStrategy:
    def __init__(self):
        self.strategy_id = "quant_$2"
        self.active_limits = {}

    async def evaluate_market(self, market_id: str, mid_price: float):
        """
        Pure mathematical pipeline intercept structure.
        Bypass heavy language generation via quant thresholds.
        """
        return {"status": "skipped", "edge": 0.0, "reason": "Unimplemented quantitative mapping"}

# Active singleton injection reference
${2}_trader = ${2^}QuantitativeStrategy()
EOF
    echo ">> [SCAFFOLD] Template injected securely!"
}

case "$1" in
    setup) setup ;;
    vibe) vibe ;;
    launch) launch ;;
    stop) stop ;;
    dashboard) dashboard ;;
    scaffold) scaffold "$@" ;;
    *) show_help ;;
esac
