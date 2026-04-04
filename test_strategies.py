import asyncio
from src.strategies.market_maker import MarketMaker
from src.strategies.copy_trader import CopyTrader
from risk_manager import RiskManager

async def test_strategies():
    print("==================================")
    print(" STRATEGIES EXECUTOR: INTEGRATION ")
    print("==================================")

    # We use a purely Mock KalshiClient to verify that the strategies execute correct payloads dynamically
    class MockKalshi:
        async def place_order(self, market_id, side, count_cents, yes_price):
            return {"status": "simulated_hardware", "market": market_id, "side": side, "cents": count_cents, "limit": yes_price}

    risk = RiskManager()
    kalshi = MockKalshi()
    
    mm = MarketMaker(kalshi_client=kalshi, risk_manager=risk)
    copy = CopyTrader(kalshi_client=kalshi, risk_manager=risk)
    
    market_id = "KX-RATES-DEC"
    
    print("\n------------------------------")
    print(" 1. TESTING MARKET MAKER SKEW ")
    print("------------------------------")
    # If the LLM Debate Engine says the true price is 88 cents...
    mm_res = await mm.provide_liquidity(market_id, inferred_probability=0.88)
    print(f"\n[+] Raw MarketMaker Hardware Dump:\n{mm_res}")
    
    print("\n------------------------------")
    print(" 2. TESTING COPY TRADER KELLY ")
    print("------------------------------")
    # Simulate an external webhook dropping in showing a massive Whale execution
    fake_discord_webhook = [
        {"trader": "@KalshiWhale_99", "action": "buy", "amount": 9000.0, "price_cents": 62}
    ]
    copy_res = await copy.execute_copy_trading_cycle(market_id, fake_discord_webhook)
    print(f"\n[+] Raw CopyTrader Hardware Dump:\n{copy_res}")

if __name__ == "__main__":
    asyncio.run(test_strategies())
