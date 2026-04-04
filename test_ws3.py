import asyncio
import json
import websockets
import ssl
import certifi
from kalshi_client_wrapper import KalshiClientWrapper

async def test_ws_verify():
    wrapper = KalshiClientWrapper()
    async with wrapper as client:
        markets = await client.get_active_markets()
        if not markets: return
        test_ticker = markets[0]['id']
        
    wss_url = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    auth_headers = wrapper._generate_headers("GET", "/ws/v2")
    
    auth_payload = json.dumps({
        "id": 1,
        "cmd": "authenticate"
    })
    
    subscribe_payload = json.dumps({
        "id": 2,
        "cmd": "subscribe",
        "params": {
            "channels": ["ticker"],
            "market_tickers": [test_ticker]
        }
    })
    
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with websockets.connect(wss_url, ssl=ssl_context, extra_headers=auth_headers) as websocket:
        await websocket.send(auth_payload)
        await websocket.send(subscribe_payload)
        count = 0
        async for message in websocket:
            print(message)
            count += 1
            if count >= 3:
                break

asyncio.run(asyncio.wait_for(test_ws_verify(), 5))
