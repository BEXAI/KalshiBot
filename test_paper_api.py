import asyncio
from kalshi_client_wrapper import KalshiClientWrapper

async def run_tests():
    print("==================================")
    print(" KALSHI CLIENT ADVANCED TESTS     ")
    print("==================================")
    
    # We now strictly instantiate the client wrapper inside an async context manager
    async with KalshiClientWrapper() as client:
        print(f"\nTargeting Environment: {client.base_url}")
        
        print("\n--- Test 1: Fetch Balance (Session Pool Check) ---")
        balance_res = await client.get_balance()
        print(f"HTTP Status: {balance_res['status']}")
        if balance_res['status'] == 200:
            print("SUCCESS! Session pooling working correctly.")
        
        print("\n--- Test 2: Fetch Active Markets (Open Data Check) ---")
        markets = await client.get_active_markets()
        print(f"Successfully retrieved {len(markets)} active markets via session pool.")
        
        print("\n--- Test 3: Simulated Paper Order Placement ---")
        # Attempting to explicitly buy NO contracts. 50 contracts (cents).
        if markets:
            market_ticker = markets[0]['id']
            print(f"Attempting Paper Execution targeting {market_ticker}...")
            order_res = await client.place_order(
                market_id=market_ticker,
                side="buy", 
                amount_cents=50,
                limit_price_cents=10
            )
            print(f"Result: {order_res}")
        
    print("\n==================================")
    print(" API SANDBOX TEST COMPLETE        ")
    print("==================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
