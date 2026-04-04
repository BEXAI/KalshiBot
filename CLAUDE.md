# KalshiBot - Autonomous Trading System Architecture

## CORE ARCHITECTURE & ROUTING
This repository is an Advanced Agentic Trading Bot running on Apple M4 Silicon natively bypassing heavy pipelines for qualitative efficiency via hyper-fast execution loops.

**IMPORTANT:** The execution stream is split inherently:
1. **Agentic Pipeline (LangGraph):** Routes heavy predictive probability markets through standard Open-Weight local models (via Ollama/Llama).
2. **Quant Fast-Path:** Natively bypasses LangGraph queues for deterministically quantifiable models. 
   - Example (`KXTEMP...`): Sweeps natively out of the WebSocket onto `weather_trader.py` (GFS-31 Member limits).

## BUILD & TEST WORKFLOW
- **ALWAYS** use `./kalshi-manager.sh` to execute environment routines natively.
- **NEVER** launch standard python binaries directly outside the `.venv3.nosync` array unless testing headless.
- Install native dependencies dynamically: `pip install -r requirements.txt`.

### Key Dev Commands
```bash
bash kalshi-manager.sh setup   # Maps Native Arrays & Dependencies
bash kalshi-manager.sh vibe    # Loads Claude Session directly
bash start_daemon.sh           # Binds daemon securely to background (production)
```

## CODING STANDARDS & ETIQUETTE
- **YOU MUST** maintain absolute modularity. Strategies are located cleanly in `src/strategies/`.
- **CRITICAL:** Use `aiohttp` or standard `KalshiClient` functions strictly async (`async/await`) without creating isolated thread pools that block `asyncio` loops!
- Use 4-space indentation and explicit type hinting where structurally viable (`market_id: str, mid_price: float`).
- Natively log all execution structures into `kalshi_trades.jsonlines` asynchronously via JSON dictionary appending.

## SECURITY & ENVIRONMENTS
- `PAPER_MODE` is strictly sourced from `.env` globally before execution.
- RSA-PSS signing handles standard transaction hashes. 
- **CRITICAL:** Do NOT expose production Kalshi payloads in GitHub environments! Always mask arrays locally.

## PROJECT EXPLORATION RULES
- **ALWAYS** utilize the "Explore -> Plan -> Code -> Verify -> Commit" structured workflow.
- DO NOT blindly overwrite architectural graphs in `trading_agent.py` without parsing the LLM debate synthesis dependencies!
