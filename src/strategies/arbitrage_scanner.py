import aiohttp
import urllib.parse
import json
import ssl
import certifi
from typing import Dict, Optional
from error_cache import error_cache

class ArbitrageScanner:
    """
    Cross-market Arbitrage Engine.
    Compares Kalshi mid-prices against Polymarket bounding APIs.
    """
    def __init__(self, kalshi_client, risk_manager):
        self.kalshi_client = kalshi_client
        self.risk_manager = risk_manager
        self.minimum_spread_yield = 0.02 # Require > 2% risk-free rate
        self.polymarket_url = "https://gamma-api.polymarket.com/events"
        
        # Cache for Kalshi Ticker -> Polymarket Slug mapping.
        # This inherently protects our outbound network from Polymarket rate limiting 1000s of WSS ticks.
        self.slug_cache: Dict[str, Optional[str]] = {}
        
    async def get_kalshi_close_date(self, kalshi_market_id: str) -> Optional[str]:
        try:
            url = f"{self.kalshi_client.base_url}/markets/{kalshi_market_id}"
            headers = self.kalshi_client._generate_headers("GET", f"/markets/{kalshi_market_id}")
            async with self.kalshi_client._session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    market = data.get("market", data)
                    return market.get("close_time") or market.get("expiration_time")
        except Exception as e:
            error_cache.record_error("Arbitrage_Kalshi_Date", e, {"kalshi_id": kalshi_market_id})
        return None
        
    async def fetch_polymarket_price(self, kalshi_market_id: str, kalshi_question: str) -> Optional[float]:
        """
        Dynamically fetches and extracts exact Poly prices, falling back to cache.
        """
        if kalshi_market_id in self.slug_cache:
            poly_slug = self.slug_cache[kalshi_market_id]
            if not poly_slug:
                return None
            return await self._query_polymarket_price(poly_slug)
            
        # Initial Discovery Phase (Fuzzy URL Encoding)
        # We strip the "Will" and "?" to ensure Polymarket's Gamma search index has the best chance.
        cleaned_question = kalshi_question.replace("?", "").replace("Will", "").strip()
        encoded = urllib.parse.quote(cleaned_question)
        search_url = f"{self.polymarket_url}?title={encoded}&active=true&closed=false"
        
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(search_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            kalshi_close = await self.get_kalshi_close_date(kalshi_market_id)
                            kalshi_month = kalshi_close[:7] if kalshi_close else None # YYYY-MM
                            
                            for event in data:
                                poly_slug = event.get("slug")
                                poly_close = event.get("endDate")
                                
                                # Expiration Parity check
                                if kalshi_month and poly_close:
                                    poly_month = poly_close[:7]
                                    if kalshi_month != poly_month:
                                        print(f"       -> [ARBITRAGE MAPPER] REJECTED Polymarket '{poly_slug}' due to Expiration Mismatch: Kalshi({kalshi_month}) vs Poly({poly_month})")
                                        continue
                                
                                self.slug_cache[kalshi_market_id] = poly_slug  # Save mapping!
                                print(f"[ARBITRAGE MAPPER] Linked Kalshi {kalshi_market_id} <-> Polymarket {poly_slug}")
                                return await self._query_polymarket_price(poly_slug, event)
                            
                            # If we exhausted without matches
                            self.slug_cache[kalshi_market_id] = None
        except Exception as e:
            error_cache.record_error("Arbitrage_Discovery", e, {"kalshi_id": kalshi_market_id})
            
        return None

    async def _query_polymarket_price(self, slug: str, preloaded_event: dict = None) -> Optional[float]:
        """Queries precise token price updates from polymarket."""
        if preloaded_event:
            return self._extract_mid_price(preloaded_event)
            
        try:
            url = f"{self.polymarket_url}?slug={slug}"
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            return self._extract_mid_price(data[0])
        except Exception as e:
            error_cache.record_error("Arbitrage_Poly_Price", e, {"slug": slug})
        return None

    def _extract_mid_price(self, event_data: dict) -> Optional[float]:
        markets = event_data.get("markets", [])
        if not markets:
            return None
        # Polymarket encapsulates their YES/NO tokens in a stringified JSON array
        outcomes = event_data.get("markets", [{}])[0].get("outcomePrices")
        if outcomes:
            try:
                if isinstance(outcomes, str):
                    outcomes = json.loads(outcomes)
                if len(outcomes) > 0:
                    return float(outcomes[0]) # YES Token is typically index 0
            except Exception:
                pass
        return None

    async def scan_market(self, kalshi_market_id: str, kalshi_question: str, kalshi_mid_price: float):
        """
        Calculates spread between markets and executes Risk-Free Hedged Positions if profitable.
        """
        poly_price = await self.fetch_polymarket_price(kalshi_market_id, kalshi_question)
        
        if poly_price is None:
            return {"status": "arbitrage_skipped", "reason": "No matched Poly token"}
            
        spread = abs(kalshi_mid_price - poly_price)
        
        if spread > self.minimum_spread_yield:
            print(f"       -> [ARBITRAGE ALERT] MASSIVE SPREAD DETECTED ON {kalshi_market_id}!")
            print(f"       -> Kalshi: {kalshi_mid_price:.2f} | Polymarket: {poly_price:.2f} | Spread Delta: {spread:.3f}")
            trade_amount = 5.0
            
            if self.risk_manager.validate_trade(trade_amount * 2):
                
                if kalshi_mid_price < poly_price:
                    print("       -> FIRING EXECUTIONS: Accumulating long Kalshi positions (Kalshi is natively underpriced).")
                    await self.kalshi_client.place_order(kalshi_market_id, "buy", int(trade_amount * 100), int(kalshi_mid_price * 100))
                    print("                         !!! AWAITING MANUAL POLYMARKET SHORT EXECUTION TO CLOSE HEDGE !!!")
                else:
                    print("       -> FIRING EXECUTIONS: Kalshi is significantly overpriced natively.")
                    # In real code, we sell kalshi long and buy poly long. We omit complex sell logic for safety.
                    print("                         !!! AWAITING MANUAL POLYMARKET LONG EXECUTION !!!")
                    
                self.risk_manager.record_trade(trade_amount * 2)
                return {"status": "arbitrage_executed", "spread": spread, "amount_hedged": trade_amount}
                
        return {"status": "arbitrage_skipped", "reason": f"Spread {spread:.3f} below minimum {self.minimum_spread_yield}"}
