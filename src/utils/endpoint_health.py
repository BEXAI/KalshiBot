import asyncio
import sys
import os

# Secure structural routing into master architecture
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kalshi_client_wrapper import KalshiClientWrapper

async def audit_endpoints():
    """
    Actively polls Kalshi V2 endpoints natively to enforce payload schema.
    Halts continuous deployment if structural parity is severed.
    """
    print("\n>>> INITIALIZING KALSHI API ENDPOINT HEALTH CHECK <<<")
    
    try:
        async with KalshiClientWrapper() as kc:
            print("\n[TEST 1] REST /markets Parity... 📡")
            markets = await kc.get_active_markets()
            if not markets or "id" not in markets[0]:
                raise ValueError("REST Schema /markets dropped expected 'id' payload structurally.")
            print("[✓] REST API Operational. Fetched live active target arrays.")
            
            print("\n[TEST 2] WebSocket Stream Structural Payload Validation... 📡")
            count = 0
            has_snapshot = False
            
            # Utilize a hard timeout proxy enforcing pipeline to avoid infinite hangs natively
            async def pull_wss():
                nonlocal count, has_snapshot
                async for tick in kc.connect_and_stream():
                    if "type" not in tick:
                         raise ValueError("WSS payload entirely missing 'type' identity boundary.")
                    
                    msg_type = tick["type"]
                    # Assert V2 structural arrays dynamically
                    if msg_type in ["orderbook_delta", "orderbook_snapshot", "ticker"]:
                        if "msg" not in tick:
                            raise ValueError(f"WSS Payload for {msg_type} is explicitly missing 'msg' wrapper envelope!")
                        
                        has_snapshot = True
                        
                    count += 1
                    if count >= 8 and has_snapshot:
                        break

            # If Kalshi API natively freezes or rate-limits, this crashes appropriately
            await asyncio.wait_for(pull_wss(), timeout=10.0)
            print("[✓] WebSocket V2 Structural Schema Passed (Located JSON Envelope bounds correctly).")
            
            print("\n>>> ALL API SYSTEMS VERIFIED GREEN <<<")
            
    except asyncio.exceptions.TimeoutError:
        print("\n[!] CRITICAL ERROR: WebSocket feed natively hanged or rate limited heavily. Refusing daemon launch.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] CRITICAL ERROR: API Connection boundaries explicitly violated natively: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(audit_endpoints())
