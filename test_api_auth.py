import asyncio
import os
import json
from settings import settings
from kalshi_client_wrapper import KalshiClientWrapper

async def test_auth():
    print(f"[TEST] Using ENV: {settings.KALSHI_ENV} - URL: {settings.KALSHI_API_URL}")
    print(f"[TEST] Key ID: {settings.KALSHI_API_KEY_ID[:5]}... (Redacted)")
    
    if not os.path.exists(settings.KALSHI_PRIVATE_KEY_PATH):
        print(f"[ERROR] Absolutely no .pem key file found at: {settings.KALSHI_PRIVATE_KEY_PATH}")
        return
        
    print(f"[TEST] Found .pem file at {settings.KALSHI_PRIVATE_KEY_PATH}. Proceeding to contact Live Exchange...")
    
    try:
        async with KalshiClientWrapper() as client:
            bal_resp = await client.get_balance()
            print("\n----- API BALANCE RESPONSE -----")
            print(json.dumps(bal_resp, indent=2))
            
            markets = await client.get_active_markets()
            print("\n----- API MARKETS RESPONSE (First 2) -----")
            print(json.dumps(markets[:2], indent=2))
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR EXCEPTION]: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())
