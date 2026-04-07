import asyncio
import json
import os
import certifi
import time
import pydantic.v1 # Fixes Python 3.13 deadlock via langchain_core

# Hotfix for macOS unverified aiohttp contexts inside Kalshi SDK / Gemini
os.environ['SSL_CERT_FILE'] = certifi.where()

from kalshi_client_wrapper import KalshiClientWrapper
from risk_manager import RiskManager
from trading_agent import TradingAgent
from src.strategies.arbitrage_scanner import ArbitrageScanner
from src.strategies.market_maker import MarketMaker
from src.strategies.momentum_rider import MomentumRider
from src.strategies.timesfm_forecaster import TimesFMForecaster
from src.strategies.weather_trader import WeatherTrader
from settings import settings
from filter_engine import TickAggregator
from error_cache import error_cache

async def main():
    print("===================================================")
    print(" Initializing Agentic AI Kalshi Trading Bot        ")
    print("===================================================")
    
    # Core orchestration objects
    risk_manager = RiskManager()
    
    # Lowered drift threshold to 0.2% + 10-minute time floor to guarantee ~6 trades/hour
    tick_aggregator = TickAggregator(threshold=0.002)
    output_file = "kalshi_trades.jsonlines"
    
    # Single Semaphore for AI Concurrency Limit
    ai_semaphore = asyncio.Semaphore(5)
    
    # Open the Single Connection Pool Master Lifecycle
    async with KalshiClientWrapper() as kalshi_client:
        
        # Instantiate Algorithmic Predictor Rules
        timesfm_forecaster = None
        if settings.TIMESFM_ENABLED:
            timesfm_forecaster = TimesFMForecaster(
                context_len=settings.TIMESFM_MIN_HISTORY,
                horizon_len=settings.TIMESFM_HORIZON,
                cooldown_seconds=settings.TIMESFM_COOLDOWN
            )

        # Inject the context pool downward into all agents
        agent = TradingAgent(kalshi_client=kalshi_client, risk_manager=risk_manager, timesfm_forecaster=timesfm_forecaster)
        arbitrage = ArbitrageScanner(kalshi_client=kalshi_client, risk_manager=risk_manager)
        market_maker = MarketMaker(kalshi_client=kalshi_client, risk_manager=risk_manager)
        momentum_rider = MomentumRider(kalshi_client=kalshi_client, risk_manager=risk_manager)
        weather_trader = WeatherTrader(kalshi_client=kalshi_client, risk_manager=risk_manager)
        
        print(f"Connected Master Session Pool targeting {kalshi_client.base_url}")
        print("Launching live WebSocket streams...")
        
        # Dual-Loop Asynchronous Central Memory Bound
        SHARED_STRATEGY_STATE = {}
        
        # Iterating over the live market ticker event loop stream!
        while True:
            try:
                count = 0
                async for tick in kalshi_client.connect_and_stream():
                    if not tick or "type" not in tick:
                        continue
                        
                    msg_type = tick.get("type")
                    
                    if msg_type in ["orderbook_delta", "orderbook_snapshot"]:
                        ob_data = tick.get("msg", {})
                        ob_market = ob_data.get("market_ticker")
                        if ob_market and tick_aggregator.is_strategic_market(ob_market):
                            if tick_aggregator.is_toxic_market_id(ob_market):
                                continue
                            
                            # --- SOTA ASYNC DUAL LOOP: FAST EXECUTION! ---
                            # The loop instantaneously polls the slow macro reasoning strategy logic without blocking!
                            strategy = SHARED_STRATEGY_STATE.get(ob_market, {"bias": "HOLD"})
                            if strategy["bias"] != "HOLD" and timesfm_forecaster:
                                tfm_proj_hist = timesfm_forecaster.tick_buffers.get(ob_market)
                                if tfm_proj_hist and len(tfm_proj_hist) > 0:
                                    target_mean = sum(tfm_proj_hist) / len(tfm_proj_hist)
                                    best_ask = 100
                                    asks = ob_data.get('yes_asks', [])
                                    if asks: best_ask = min([p for p, q in asks if q > 0] or [100])
                                    
                                    # Target Fast Edge Logic
                                    if strategy["bias"] == "LONG_YES" and (target_mean - (best_ask/100.0)) >= settings.MIN_EDGE:
                                        exec_size = int(strategy.get("amount", 1.0) * 100)
                                        print(f"⚡ [HFT EXECUTE] BUY {exec_size} YES {ob_market} @ {best_ask}c | TFM Target: {target_mean*100:.1f}c")
                                        if not settings.PAPER_MODE:
                                            await kalshi_client.place_order(ob_market, "buy", exec_size, best_ask)
                                        SHARED_STRATEGY_STATE[ob_market] = {"bias": "HOLD"}
                                        
                                    elif strategy["bias"] == "LONG_NO":
                                        best_no_ask = 100
                                        no_asks = ob_data.get('no_asks', [])
                                        if no_asks: best_no_ask = min([p for p, q in no_asks if q > 0] or [100])
                                        no_target = 1.0 - target_mean
                                        if (no_target - (best_no_ask/100.0)) >= settings.MIN_EDGE:
                                            exec_size = int(strategy.get("amount", 1.0) * 100)
                                            print(f"⚡ [HFT EXECUTE] BUY {exec_size} NO {ob_market} @ {best_no_ask}c | TFM Target NO: {no_target*100:.1f}c")
                                            if not settings.PAPER_MODE:
                                                await kalshi_client.place_order(ob_market, "buy", exec_size, best_no_ask, contract_side="no")
                                            SHARED_STRATEGY_STATE[ob_market] = {"bias": "HOLD"}
                            
                            ob_imbalance = tick_aggregator.track_orderbook(ob_market, ob_data)
                            if ob_imbalance > 3.0:
                                await momentum_rider.evaluate_momentum_imbalance(ob_market, ob_imbalance)
                        continue
                        
                    if msg_type != "ticker":
                        continue
                    
                    ticker_data = tick.get("msg", {})
                    market_id = ticker_data.get("market_ticker")
                    if not market_id:
                        continue
                    
                    # 1. Broad Strategic Whitelist Filter
                    if not tick_aggregator.is_strategic_market(market_id):
                        continue
                        
                    # 1.5 Multi-Game & Cross-Category Strict Filter Check
                    if tick_aggregator.is_toxic_market_id(market_id):
                        continue
                    
                    # Simple UI heartbeat tick every 20 target events
                    count += 1
                    if count % 20 == 0:
                        print(f"[HEARTBEAT] WSS feed active. Just parsed target tick for {market_id}")
                    
                    y_ask = ticker_data.get('yes_ask', 50)
                    y_bid = ticker_data.get('yes_bid', 50)
                    mid_cents = float((y_ask + y_bid) / 2)
                    mid_price = mid_cents / 100.0
                    
                    # Ensure ROI profitability bounds to prevent inefficient compute drops
                    if not tick_aggregator.is_profitable_bounds(mid_price):
                        continue
                        
                    # 2. Evaluate High-Velocity Momentum Loop continuously
                    await momentum_rider.evaluate_momentum(market_id, mid_price)
                    
                    if timesfm_forecaster:
                        timesfm_forecaster.record_tick(market_id, mid_price)
                        
                    # 3. Dynamic Volatility Drift Filter (Bypass static throttle)
                    if not tick_aggregator.should_trigger_ai(market_id, mid_price):
                        continue
                    
                    print(f"\n[EVENT] Volatility drift threshold broken for {market_id}. Executing Heavy AI Inference!")
                    
                    market_title = await kalshi_client.get_market_title(market_id)
                    
                    # Prevent arbitrary Combo or Multi-Leg titles from entering single-variable AI model strings
                    if tick_aggregator.is_toxic_market(market_title):
                        print(f"[FILTER] Dropped toxic combo market natively: {market_title}")
                        continue
                    
                    market_state = {
                        "id": market_id,
                        "question": market_title,
                        "mid_price": mid_price
                    }
                    
                    # Execute Heavy AI Strategy Pipeline without blocking the WebSocket
                    # Bind loop variables via default args to avoid stale closure capture
                    async def process_market_event(_mid=market_id, _ms=market_state):
                        async with ai_semaphore:
                            try:
                                current_time = time.time()
                                
                                # 1. Fast-Path Bypass for Pure Mathematical Models
                                if "KXTEMP" in _mid:
                                    balance_res = await kalshi_client.get_balance()
                                    raw_balance = balance_res.get("data", {}).get("balance", 0) / 100.0
                                    wt_result = await weather_trader.evaluate_weather_market(_mid, _ms["mid_price"], raw_balance)
                                    
                                    combined_audit = {
                                        "market": _mid,
                                        "timestamp": current_time,
                                        "strategy_type": "hybrid_quant_weather",
                                        "weather_sweep": wt_result
                                    }
                                    
                                    with open(output_file, "a") as f:
                                        f.write(json.dumps(combined_audit) + "\n")
                                    print(f"[EVENT] Saved meteorological quant state audit for {_mid}")
                                    return # Abort further LLM processing entirely for efficiency 

                                # 2. Heavy AI Strategy Pipeline for Standard Prediction Markets
                                final_state = await agent.run_market_cycle(_ms)

                                # EXPORT SOTA OVERARCHING STRATEGY TO FAST LOOP
                                decision = final_state.get("decision", "SKIP")
                                if decision in ["TRADE", "PAPER_TRADE"]:
                                    bias = "LONG_YES" if final_state["llm_prob"] > 0.5 else "LONG_NO"
                                    # Export asynchronous strategic parameters silently!
                                    SHARED_STRATEGY_STATE[_mid] = {
                                        "bias": bias,
                                        "confidence": final_state["llm_prob"],
                                        "amount": final_state.get("trade_amount", 1.0)
                                    }
                                    print(f"🧠 [AGENT STRATEGY UPDATE] {_mid} -> Bias: {bias} queued.")

                                arb_result = await arbitrage.scan_market(_mid, _ms["question"], _ms["mid_price"])
                                mm_result = await market_maker.provide_liquidity(_mid, final_state['llm_prob'])
                                
                                combined_audit = {
                                    "market": _mid,
                                    "timestamp": current_time,
                                    "strategy_type": "llm_agentic_prediction",
                                    "debate_inference": final_state,
                                    "arbitrage_sweep": arb_result,
                                    "market_making_sweep": mm_result
                                }

                                with open(output_file, "a") as f:
                                    f.write(json.dumps(combined_audit) + "\n")

                                print(f"[EVENT] Saved comprehensive state audit for {_mid}")
                            except Exception as e:
                                error_cache.record_error("MasterLoop_Pipeline", e, {"market_id": _mid})

                    asyncio.create_task(process_market_event())
            except asyncio.exceptions.CancelledError:
                print(f"[SHUTDOWN] WSS Stream successfully cancelled natively.")
                break
            except Exception as conn_err:
                print(f"[CRITICAL] Global WebSocket feed interrupted: {conn_err}. Recovering natively in 5s...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
