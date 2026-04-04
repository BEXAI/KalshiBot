import os
import websockets
import json
import aiohttp
import ssl
import certifi
import uuid
import time
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from settings import settings
from error_cache import error_cache

class KalshiClientWrapper:
    """
    Wrapper for Kalshi client initialization utilizing NO-SDK raw aiohttp logic.
    """
    def __init__(self):
        # We target explicitly based on settings.py Environment Parity config
        if settings.KALSHI_ENV.lower() == "production":
            self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        else:
            self.base_url = "https://demo-api.kalshi.co/trade-api/v2"
            
        try:
            with open(settings.KALSHI_PRIVATE_KEY_PATH, "rb") as f:
                self.private_key = load_pem_private_key(f.read(), password=None)
        except Exception as e:
            print(f"[AUTH ERROR] Failed to load private key from {settings.KALSHI_PRIVATE_KEY_PATH}: {e}")
            self.private_key = None
            
        self._session = None
        self._market_title_cache = {}  # ticker -> title, fetched once per market

    async def __aenter__(self):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()

    def _generate_headers(self, method: str, path: str):
        timestamp = str(int(time.time() * 1000))
        # Kalshi V2 api expects the full uri path. wss endpoints use /trade-api/ws/v2
        if path.startswith("/ws"):
            full_path = "/trade-api" + path
        else:
            full_path = "/trade-api/v2" + path
        msg_string = timestamp + method + full_path
        
        if not self.private_key:
            return {"Content-Type": "application/json"}
        
        signature = self.private_key.sign(
            msg_string.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        encoded_sig = base64.b64encode(signature).decode('utf-8')
        return {
            "KALSHI-ACCESS-KEY": settings.KALSHI_API_KEY_ID,
            "KALSHI-ACCESS-SIGNATURE": encoded_sig,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

    async def get_balance(self) -> dict:
        """
        Fetches the portfolio balance to verify authentication.
        """
        if not self._session:
            raise RuntimeError("KalshiClientWrapper must be used as an async context manager.")
            
        try:
            path = "/portfolio/balance"
            url = f"{self.base_url}{path}"
            headers = self._generate_headers("GET", path)
            
            async with self._session.get(url, headers=headers) as response:
                data = await response.json()
                return {"status": response.status, "data": data}
        except Exception as e:
            error_cache.record_error("KalshiClientWrapper", e, {"endpoint": "/portfolio/balance"})
            return {"status": 500, "error": str(e)}

    async def get_active_markets(self) -> list:
        """
        Fetches a slice of active, non-resolved markets to loop over, using the NO-SDK direct API approach.
        """
        if not self._session:
            raise RuntimeError("KalshiClientWrapper must be used as an async context manager.")
            
        try:
            path = "/markets"
            url = f"{self.base_url}{path}?status=open&limit=10"
            headers = self._generate_headers("GET", path)
            async with self._session.get(url, headers=headers) as response:
                data = await response.json()
                
                norm = []
                if "markets" in data:
                    for m in data["markets"]:
                        y_ask_val = m.get('yes_ask_dollars')
                        y_bid_val = m.get('yes_bid_dollars')
                        
                        y_ask = float(y_ask_val) if y_ask_val is not None else 0.50
                        y_bid = float(y_bid_val) if y_bid_val is not None else 0.50
                        
                        norm.append({
                            "id": m.get('ticker', 'UNKNOWN'),
                            "question": m.get('title', 'Unknown Title'),
                            "mid_price": float(y_ask + y_bid) / 2.0
                        })
                return norm
        except Exception as e:
            error_cache.record_error("KalshiClientWrapper", e, {"endpoint": "/markets"})
            return []

    async def place_order(self, market_id: str, side: str, amount_cents: int, limit_price_cents: int):
        """
        Places a raw limit order onto Kalshi.
        (Natively handled via raw REST payload targeting the /orders endpoint)
        """
        if not self._session:
            raise RuntimeError("KalshiClientWrapper must be used as an async context manager.")
            
        idempotency_uuid = str(uuid.uuid4())
        path = "/portfolio/orders"
        
        payload = {
            "action": side.lower(),
            "client_order_id": idempotency_uuid,
            "count": amount_cents,
            "side": "yes",
            "ticker": market_id,
            "type": "limit",
            "yes_price": limit_price_cents
        }
        
        headers = self._generate_headers("POST", path)
        print(f"[KALSHI API - NO SDK] Successfully generated idempotent payload {idempotency_uuid} for {market_id}")
        
        # Protect Capital if explicitly in Paper Trading 
        if settings.PAPER_MODE:
            print(f"[PAPER MODE EXECUTION] Simulated order placement: {side} {amount_cents} contracts on {market_id} @ {limit_price_cents}c.")
            return {"status": "simulated", "order_id": idempotency_uuid}
            
        url = f"{self.base_url}{path}"
        try:
            async with self._session.post(url, json=payload, headers=headers) as response:
                resp_data = await response.json()
                return {"status": response.status, "data": resp_data}
        except Exception as e:
            error_cache.record_error("KalshiClientWrapper", e, {"endpoint": "/portfolio/orders", "market": market_id})
            return {"status": 500, "error": str(e)}

    async def get_market_title(self, ticker: str) -> str:
        """
        Fetches and caches the human-readable market title for a ticker.
        Falls back to ticker ID if the API call fails.
        """
        if ticker in self._market_title_cache:
            return self._market_title_cache[ticker]

        if not self._session:
            return ticker

        try:
            path = f"/markets/{ticker}"
            url = f"{self.base_url}{path}"
            headers = self._generate_headers("GET", path)
            async with self._session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    market = data.get("market", data)
                    title = market.get("title") or market.get("question") or ticker
                    self._market_title_cache[ticker] = title
                    return title
        except Exception as e:
            error_cache.record_error("KalshiClientWrapper", e, {"endpoint": f"/markets/{ticker}"})

        self._market_title_cache[ticker] = ticker
        return ticker

    async def cancel_order(self, order_id: str):
        """
        Cancels a specific resting order to clear toxic liquidity.
        """
        if not self._session:
            raise RuntimeError("KalshiClientWrapper must be used as an async context manager.")
            
        if settings.PAPER_MODE:
            print(f"[PAPER MODE EXECUTION] Simulated order cancellation: {order_id}")
            return {"status": "simulated", "order_id": order_id}
            
        path = f"/portfolio/orders/{order_id}"
        headers = self._generate_headers("DELETE", path)
        
        url = f"{self.base_url}{path}"
        try:
            async with self._session.delete(url, headers=headers) as response:
                resp_data = await response.json()
                return {"status": response.status, "data": resp_data}
        except Exception as e:
            error_cache.record_error("KalshiClientWrapper", e, {"endpoint": f"/portfolio/orders/{order_id}"})
            return {"status": 500, "error": str(e)}

    async def connect_and_stream(self):
        """
        Connects to Kalshi's wss endpoint natively and yields real-time ticker data.
        In production, RSA signing headers are mandated by the payload spec.
        """
        if settings.KALSHI_ENV.lower() == "production":
            wss_url = "wss://api.elections.kalshi.com/trade-api/ws/v2"
        else:
            wss_url = "wss://demo-api.kalshi.co/trade-api/ws/v2"
            
        # We inject Kalshi RSA headers as extra_headers during the WSS HTTP handshake
        auth_headers = self._generate_headers("GET", "/ws/v2")
        
        auth_payload = json.dumps({
            "id": 1,
            "cmd": "authenticate"
        })
        
        subscribe_payload = json.dumps({
            "id": 2,
            "cmd": "subscribe",
            "params": {"channels": ["ticker"]} # We subscribe global tick data
        })
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        try:
            async with websockets.connect(wss_url, ssl=ssl_context, extra_headers=auth_headers) as websocket:
                print(f"[WebSocket] Connected to {wss_url}. Transmitting authenticate & subscribe commands...")
                await websocket.send(auth_payload)
                await websocket.send(subscribe_payload)
                
                # Infinite generator yielding market ticks
                async for message in websocket:
                    yield json.loads(message)
        except Exception as e:
            print(f"[WebSocket] Error listening to Kalshi streams: {e}")
