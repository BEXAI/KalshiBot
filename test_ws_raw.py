import asyncio
import json
import websockets
import ssl
import certifi

async def test_ws():
    wss_url = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    subscribe_payload = json.dumps({
        "id": 1,
        "cmd": "subscribe",
        "params": {
            "channels": ["ticker"]
        }
    })
    
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        async with websockets.connect(wss_url, ssl=ssl_context) as websocket:
            await websocket.send(subscribe_payload)
            print("Sent subscribe")
            count = 0
            async for message in websocket:
                print(message)
                count += 1
                if count >= 3:
                    break
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_ws())
