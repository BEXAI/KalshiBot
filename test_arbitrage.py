import asyncio
from src.strategies.arbitrage_scanner import ArbitrageScanner
from risk_manager import RiskManager

async def test_arbitrage():
    print("==================================")
    print(" ARBITRAGE ENGINE: NETWORK TEST   ")
    print("==================================")
    
    # We mock out Kalshi to purely test the Polymarket REST hooks and spread mathematical logic
    class MockKalshi:
        async def place_order(self, *args, **kwargs):
            return {"status": "simulated", "mock": True}
            
    risk_manager = RiskManager()
    scanner = ArbitrageScanner(kalshi_client=MockKalshi(), risk_manager=risk_manager)
    
    kalshi_id = "KX-RATES-24" # Mock internal ID
    kalshi_q = "Will the US enter a recession in 2024?" # Real Polymarket question structure
    kalshi_mid = 0.50 # Let's say Kalshi thinks it's 50%
    
    print(f"\n[+] Connecting to Polymarket Gamma API to locate dual-market match for: '{kalshi_q}'")
    
    # Test 1: Active query hitting the internet
    res = await scanner.scan_market(kalshi_id, kalshi_q, kalshi_mid)
    print(f"\n[+] RESULT 1: {res}")
    
    print("\n[+] Triggering secondary tick evaluation. This MUST pull gracefully from slug_cache without network delay!")
    
    # Test 2: Ensure the ID dictionary caches prevent DDOS
    res2 = await scanner.scan_market(kalshi_id, kalshi_q, kalshi_mid)
    print(f"\n[+] RESULT 2: {res2}")

if __name__ == "__main__":
    asyncio.run(test_arbitrage())
