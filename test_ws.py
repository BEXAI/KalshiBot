import asyncio
import json
from filter_engine import TickAggregator

async def monitor_stream():
    from kalshi_client_wrapper import KalshiClientWrapper
    
    wrapper = KalshiClientWrapper()
    aggregator = TickAggregator(threshold=0.03)

    print("Initializing Kalshi AI WebSocket Integration Test...")
    
    # We simulate a stream connection. (In reality, we won't wait infinitely here to keep tests clean)
    async for tick in wrapper.connect_and_stream():
        msg_type = tick.get("type")
        if not msg_type:
            continue
            
        if msg_type == "orderbook_delta":
            ob_data = tick.get("orderbook_delta", {})
            ob_market = ob_data.get("market_id")
            if ob_market and aggregator.is_strategic_market(ob_market):
                ob_imbalance = aggregator.track_orderbook(ob_market, ob_data)
                print(f"[TEST L2] {ob_market} Book Imbalance Ratio: {ob_imbalance:.2f}:1")
            continue
            
        if msg_type == "market_ticker":
            ticker_data = tick.get("ticker", {})
            market_id = ticker_data.get("ticker", "UNKNOWN")
            y_ask = ticker_data.get('yes_ask', 50)
            y_bid = ticker_data.get('yes_bid', 50)
            price = ((y_ask + y_bid) / 2) / 100.0
            
            if aggregator.should_trigger_ai(market_id, price):
                print(f"---- DELTA TRIGGER ----> Firing AI Debate for {market_id}!")

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(monitor_stream(), timeout=10.0))
    except asyncio.TimeoutError:
        print("\nTest completed successfully after 10s timeout.")
