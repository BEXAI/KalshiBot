import os
import json
from collections import deque
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

app = FastAPI(title="Kalshi Full Stack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TRADES_FILE = "kalshi_trades.jsonlines"
ERRORS_FILE = "kalshi_error_dump.jsonlines"

def tail_file(filename: str, n: int) -> list:
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'rb') as f:
            q = deque(f, n)
            return [line.decode('utf-8', errors='ignore') for line in q]
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

def parse_lines(lines: list) -> list:
    results = []
    for line in reversed(lines):
        try:
            results.append(json.loads(line))
        except Exception:
            pass
    return results

@app.get("/api/health")
def health_check():
    return {"status": "ok", "trades_file_exists": os.path.exists(TRADES_FILE)}

@app.get("/api/trades")
def get_trades(limit: int = 100):
    lines = tail_file(TRADES_FILE, limit)
    trades = parse_lines(lines)
    return {"trades": trades}

@app.get("/api/errors")
def get_errors(limit: int = 20):
    lines = tail_file(ERRORS_FILE, limit)
    errors = parse_lines(lines)
    return {"errors": errors}

@app.get("/api/kpis")
def get_kpis():
    # we need a bunch of trades to compute KPIs
    lines = tail_file(TRADES_FILE, 1000)
    trades = parse_lines(lines)
    
    session_pnl = 0.0
    total_trades = 0
    ai_inference_count = 0
    markets = set()
    total_edge = 0.0
    edge_count = 0
    
    for t in trades:
        market = t.get("market")
        if market:
            markets.add(market)
            
        di = t.get("debate_inference")
        if not di:
            continue
            
        decision = di.get("decision")
        if decision != "SKIP":
            ai_inference_count += 1
            
        if decision in ["TRADE", "PAPER_TRADE"]:
            total_trades += 1
            mid = di.get("market_mid_price", 0.5)
            prob = di.get("llm_prob", 0.5)
            amt = di.get("trade_amount", 0.0)
            
            if prob > mid:
                session_pnl += amt * (1.0 - mid)
            else:
                session_pnl -= amt * mid
                
            edge = di.get("edge")
            if edge is not None:
                total_edge += edge
                edge_count += 1
                
    avg_edge = (total_edge / edge_count * 100) if edge_count > 0 else 0.0
    
    return {
        "session_pnl": session_pnl,
        "total_trades": total_trades,
        "ai_inference_count": ai_inference_count,
        "active_markets": len(markets),
        "avg_edge_pct": avg_edge,
    }

@app.get("/api/pnl")
def get_pnl():
    lines = tail_file(TRADES_FILE, 200)
    trades = parse_lines(lines)
    
    running_pnl = 0.0
    chart_data = [] # { timestamp, pnl }
    
    # Process from oldest to newest
    for t in reversed(trades):
        di = t.get("debate_inference")
        if di and di.get("decision") in ["TRADE", "PAPER_TRADE"]:
            mid = di.get("market_mid_price", 0.5)
            prob = di.get("llm_prob", 0.5)
            amt = di.get("trade_amount", 0.0)
            
            if prob > mid:
                running_pnl += amt * (1.0 - mid)
            else:
                running_pnl -= amt * mid
                
            chart_data.append({
                "timestamp": t.get("timestamp"),
                "pnl": running_pnl
            })
            
    return chart_data
