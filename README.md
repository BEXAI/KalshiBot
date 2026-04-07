# BEXAI SOTA Autonomous Kalshi Trading Hub
**State-of-the-Art (SOTA) Dual-Loop High-Frequency Agent**

An ultra-low latency predictive market execution engine built for the **Kalshi V2 API**, leveraging Google's quantitative zero-shot algorithmic bounds matched against local Gemma 4 multi-agent decision chains.

---

## 🗺️ System Map: Full Stack & AI Ecosystem

### The AI & LLM Array
*   **Google TimesFM 2.5 (200M)**: Hardware-accelerated (via Apple PyTorch MPS tensors) time-series foundation model calculating continuous left-padded tick differentials dynamically across the Kalshi L2 limit matrix.  
*   **Google Gemma 4 (31B)**: The "Slow-Loop" qualitative reasoner. Processes multi-agent LangGraph debates (Bull vs. Bear personas) and bounds pure JSON risk decisions independently.
*   **Ollama Orchestrator**: Manages local inference for Gemma 4 using K/V cache pipelines natively to prevent unified VRAM depletion on Apple Silicon setups.

### API Intelligence Web
*   **Kalshi Trade API V2 (`api.elections.kalshi.com`)**: Custom *NO-SDK* HTTP endpoints employing manual RSA-PSS payload cryptography to process direct orders at absolute minimal REST weight.
*   **Kalshi WebSocket (`trade-api/ws/v2`)**: Natively ingesting `orderbook_delta` matrices to update limits fractional milliseconds ahead of institutional latency algorithms.
*   **Polymarket Gamma API (`gamma-api.polymarket.com/events`)**: Continuously mapping encoded slug paths for cross-exchange risk-free arbitrage.
*   **Open-Meteo Ensemble (`ensemble-api.open-meteo.com`)**: Bypassing LLMs explicitly by injecting strict quantified forecast limits (e.g. 31-member probabilistic weather modeling). 

### The Full Stack Monitoring Suite
*   **Backend (`dashboard_api.py`)**: A live `FastAPI` + `Uvicorn` engine tracking metrics parsed cleanly from local `kalshi_trades.jsonlines` output boundaries. 
*   **Frontend UI (`frontend/`)**: React.js / Vite terminal framework providing pure numerical dashboard visualization to monitor AI inference thresholds and PNL vectors instantly.

---

## 🧠 SOTA Architectural Philosophy (Dual-Loop)

Older AI models routinely encounter **physics bottlenecks**: LLMs require upwards of 800-1500 milliseconds to calculate inference trees, yet market limit books move in sub-milliseconds. Kalshibot eliminates this bottleneck using a **Dual-Loop Memory Architecture**. 

### Visual Execution Flow
```text
[Kalshi WebSocket] ---> Streams L2 Orderbook Data
   |
   +---> [TimesFM 2.5 Quant Loop] ---> Calculates 16-Tick Trajectory
   |
   +---> [Gemma 4 LangGraph Loop] ---> Outputs JSON {"bias": "LONG_YES"}
   |
   +---> [SHARED_STRATEGY_STATE]  <--- Synchronizes Constraints Globally
   |
   +---> [Fast-Loop Boundaries]   ---> Intersects (TimesFM Diff) vs (L2 Ask)
   |
   +---> If Difference >= MIN_EDGE ---> Executes Instant Kalshi REST Limit Orders
```

1. **The Fast Loop (Execution & Quant Boundaries)**
   Operating inside `main.py`, an aggressive WebSockets event stream tracks the raw L2 market arrays across active trackers.
   * On every L2 change, Google's `TimesFM 2.5` algorithm updates the expected 16-tick algorithmic trajectory.
   * Simultaneously, it instantly references the global `SHARED_STRATEGY_STATE` pipeline. 
   * If a `LONG_NO` or `LONG_YES` strategy from Gemma crosses the quantitative threshold gap—**(TimesFM Target Mean) - (Best Ask) >= MIN_EDGE**—the Fast Loop natively injects an execution boundary in nanoseconds! No LangGraph delays involved!

2. **The Slow Loop (Macro-Reasoning State Engine)**
   The overarching LangGraph `TradingAgent` operates continuously behind the scenes. 
   * Four zero-latency persona instances (Bull, Bear, Volatility Forecaster, Risk Management) parse global conditions without invoking network endpoints.
   * `TradingAgent` finalizes parameters across Kelly-calculated sizing limits to queue internal limit parameters seamlessly to the Fast-Loop string!

---

## 🛡️ Filtering & Security Engines

*   **Toxic Drops (`filter_engine.py`)**: Instantaneously intersects the WebSockets feed, completely rejecting multi-leg headers (e.g., `"MULTIGAME"`, `"COMBO"`, `"PARLAY"`) to avoid unpredictable "impossible calculation" inference crashes.
*   **Zero-Trust Security**: Employs raw absolute `.pem` RSA file generation locally bypassing 3rd-party Kalshi SDK library abstraction completely.
*   **Idempotency & Slip Protocols**: The Fast Loop generates algorithmic UUID tracking to guarantee a zero-double-spend environment automatically routing limits across micro-drifts dynamically.

---

## 🚀 Execution & Command Reference

**1. Boot the Master Logic Daemon (Fast + Slow Loop AI):**
```bash
cd ~/Kalshi
bash start_daemon.sh 
```
*(Executes flight-check diagnostics securely validating cryptography tokens & `.env` models before dropping directly into the L2 Orderbook stream!)*

**2. Boot the API Backbone:**
```bash
cd ~/Kalshi
bash start_fullstack.sh 
```

**3. Boot the Real-Time Viewer:**
```bash
cd ~/Kalshi/frontend
npm run dev
```

*Warning: Ensure `.env` settings map `PAPER_MODE=False` and `MIN_EDGE` logic properly before committing production hardware! Use `pkill -f main.py` when flushing loops manually to prevent recursive process clashes!*
