# BEXAI Autonomous Kalshi Trading Hub

A high-frequency predictive market execution engine built specifically for the **Kalshi V2 API**, leveraging native RSA-PSS handshake optimizations to execute dual-sided multi-agent strategies at ultra-low latency. 

## Architectural Overview

This bot abandons standard retail SDKs in favor of raw asynchronous HTTP/WebSocket sessions.

1. **NO-SDK Core (`kalshi_client_wrapper.py`)**: Establishes persistent `aiohttp` pipelines and `websockets` streams. Completely bypasses intermediate library latency by directly computing RSA-PSS header signatures natively.
2. **LangGraph Debate Matrix (`trading_agent.py`)**: State-driven LLM synthesis running locally via Ollama and verified globally via Gemini 1.5 Pro. Personas (Bull, Bear, Forecaster, Risk) evaluate the environment and synthesize true probability metrics.
3. **Filter Engine (`filter_engine.py`)**: Drops >95% of useless tick noise. Evaluates absolute price drift and L2 `orderbook_delta` resting B/A ratios to filter triggers.

## The Strategy Primitives

The codebase utilizes multiple modular attack vectors based on the LLM's determined edge:

*   **Asymmetric Market Maker (`market_maker.py`)** 
    Doesn't just passively rest. Uses Edge-Weighted Spread Skewing—aggressively leaning limit orders onto the underpriced side to capture optimal directional inventory while protecting queue positions natively against micro-drifts.
*   **Momentum Rider (`momentum_rider.py`)** 
    Reacts to early L2 volume imbalance. Implements $+1c$ spread-crossing slippage traps to guarantee fills on accelerating breakouts, accompanied by a dynamic `2-cent Trailing Stop` to protect secured premium.
*   **Arbitrage Engine (`arbitrage_scanner.py`)** 
    Continuously monitors parallel Polymarket Gamma API events, rigidly cross-checking native absolute expiration windows to safely execute risk-free spread hedges.
*   **Fractional Copy Trader (`copy_trader.py`)** 
    Listens to webhook data sources and algorithmically calculates fractional Kelly sizing boundaries to dynamically mimic historically profitable prediction whales.

## Security Warning

This repository executes over **live institutional liquidity** and demands `.pem` RSA file generation.
> **DO NOT** commit your `kalshi.pem`, `kalshi.key`, or any `.env` files into public repos. A zero-trust `.gitignore` is provided in the root to help prevent secrets exposure. 
