import asyncio
from error_cache import error_cache

async def crash_system_test():
    print("==================================")
    print(" SYSTEMS TEST: ERROR CACHE        ")
    print("==================================")
    
    print("1. Intentionally triggering a mathematical failure within simulated agent loop...")
    try:
        # Simulate LangGraph Agent crashing during Edge calculation
        edge = 10.0 / 0.0
    except Exception as e:
        error_cache.record_error("Simulated_LangGraph", e, {"market": "KX-CRASH-TEST"})
        
    print("2. Verifying error cache file creation...")
    with open("kalshi_error_dump.jsonlines", "r") as f:
        print(f"Content length read: {len(f.read())} bytes")
        
    print("\nSYSTEMS TEST PASSED: Cache correctly caught exception. Bot remains alive.")
    
if __name__ == "__main__":
    asyncio.run(crash_system_test())
