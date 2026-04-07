# KalshiBot: SOTA Dual-Loop HFT Agentic System
**Target Audience**: LLM Optimization / Context Initialization
**System Context**: Apple Silicon (M-Series Mac), Python 3.13, Local `Ollama` Node

## Executive Architecture Summary
KalshiBot is a State-of-the-Art (SOTA) asynchronous trading agent designed to solve traditional AI execution latency natively on Kalshi. It utilizes a **Dual-Loop Asynchronous Architecture** mapping sub-millisecond algorithmic L2 orderbook feeds against a macro-reasoning LLM state loop.

### 1. The Fast Loop (Execution & Quant Engine)
* **Location**: `main.py`
* **Mechanism**: Binds natively to `wss://api.elections.kalshi.com/trade-api/ws/v2` maintaining an infinite L2 Event Loop parsing `orderbook_delta` payloads. 
* **Zero-Shot Quant Analytics**: Employs Google's **TimesFM 2.5** (`timesfm_forecaster.py`) to run rolling 32-tick tensor arrays natively forecasting the next 16-ticks on the orderbook.
* **Execution Trigger**: Completely detached from slow LangGraph execution. The Fast Loop queries `SHARED_STRATEGY_STATE` asynchronously. If `target_mean - best_ask >= settings.MIN_EDGE` matches the current `LONG_YES` strategy, the loop instantly fires `kalshi_client.place_order()`.

### 2. The Slow Loop (Macro-Reasoning AI Graph)
* **Location**: `trading_agent.py` and `src/agents/debate_engine.py`
* **Mechanism**: Operates via LangGraph mapping multiple LLM persona prompts onto the local bare-metal `Ollama` framework (using `gemma4:31b`). 
* **State Queuing**: To bypass multi-second LLM processing blocking WebSocket feeds, `trading_agent.py` evaluates standard constraints and updates `SHARED_STRATEGY_STATE[market_id]` with `{"bias": "LONG_YES" | "LONG_NO", "confidence": float, "amount": float}`. It **never** executes a physical network order. 

## Component Matrix

### Infrastructure Layer
* **`kalshi_client_wrapper.py`**: A pure No-SDK zero-dependency AIOHTTP framework utilizing RSA-PSS cryptographic signing (`cryptography.hazmat`) to construct all `trade-api/v2` endpoints. Dynamically supports `"side": "yes"` and `"side": "no"`.
* **`settings.py`**: Pydantic configurations defining capital `MAX_TRADE_SIZE`, boolean `PAPER_MODE`, and the rigid `MIN_EDGE` differential fraction natively required for execution.
* **`filter_engine.py`**: Intersects all Kalshi headers natively dropping known volatile edge-cases (`"MULTIGAME"`, `"COMBO"`, `"PARLAY"`) strictly prior to expensive GPU evaluation matrices.

### Trading Strategies
* **`momentum_rider.py`**: L2 tick imbalance logic capitalizing on sub-millisecond liquidity cascades exclusively active inside the Fast Loop.
* **`weather_trader.py`**: Quantitative mapping framework pulling from `ensemble-api.open-meteo.com` bypassing LLMs entirely natively dropping matrix data directly to the execution pipeline. 
* **`arbitrage_scanner.py`**: Maps Kalshi Ticker URLs concurrently over `gamma-api.polymarket.com/events` dynamically linking token markets based on absolute Date boundaries.

### Logging & Frontend
* Local filesystem dumps into `.jsonlines` (`kalshi_trades.jsonlines`, `kalshi_error_dump.jsonlines`).
* **`dashboard_api.py`**: FastAPI backend fetching and mapping KPIs (total PNL, AI inference rate, win-rate). 
* **React/Vite (`bexai-kalshibot-dashboard`)**: Vite frontend polling endpoints running localized dynamic tracking charts tracking the state of the SOTA AI matrix.

## Development Constraints (Strict Instructions for LLMs)
1. **Ollama Locality:** Do *not* migrate backend models to HuggingFace `AutoModel` frameworks. The host runs Apple Unified Silicon. Local LLM calls strictly route via standard local REST paths.
2. **Double-Spend Protection:** Ensure the `TradingAgent` graph nodes natively push to `SHARED_STRATEGY_STATE` and *never* physically invoke API trade structures.
3. **Execution Edge:** Limit adjustments and new structural capabilities explicitly must evaluate via `target_mean` (TimesFM) against `best_ask` or `best_no_ask` bound boundaries crossing `settings.MIN_EDGE`.
