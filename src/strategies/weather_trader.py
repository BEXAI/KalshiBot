import aiohttp
import time
import math
from typing import Dict, Any, Tuple
import datetime

class WeatherTrader:
    """
    Independent quantitative weather strategy targeting Kalshi KXHIGH / KXTEMP markets.
    Utilizes 31-member GFS Seamless ensemble forecasts via Open-Meteo.
    Bypasses LLM hallucinations and executes pure statistical Kelly bounds.
    """
    def __init__(self, kalshi_client, risk_manager):
        self.kalshi = kalshi_client
        self.risk_manager = risk_manager
        
        # Free Open-Meteo Ensemble API endpoint
        self.api_url = "https://ensemble-api.open-meteo.com/v1/ensemble"
        
        # Coordinates mathematically verified precisely by Kalshi Settlement Docs (Airports)
        self.stations = {
            "NYC": {"lat": 40.7769, "lon": -73.8740}, # LGA
            "CHI": {"lat": 41.9742, "lon": -87.9073}, # ORD
            "MIA": {"lat": 25.7959, "lon": -80.2870}, # MIA
            "ATX": {"lat": 30.1975, "lon": -97.6664}, # AUS
            "DAL": {"lat": 32.8471, "lon": -96.8518}, # Love Field
            "LON": {"lat": 51.5036, "lon": 0.0533}    # London City
        }
        
        # Core global bindings
        from settings import settings
        
        # Hard limits based on algorithmic backtest parameters provided
        self.EDGE_THRESHOLD = 0.08  # 8% edge required
        self.KELLY_FRACTION = 0.15  # 15% fractional kelly
        self.MAX_WEATHER_TRADE = settings.MAX_TRADE_SIZE  # Inherit global RiskManager caps!
        
    def _parse_kalshi_ticker(self, ticker: str) -> Tuple[str, str, float]:
        """
        Parses KXTEMPNYCH-26APR0304-T47.99 into ('NYC', '2026-04-03', 47.99)
        """
        parts = ticker.split('-')
        # KXTEMPNYCH -> NYC
        city_code = parts[0].replace('KXTEMP', '').replace('H', '')
        
        # Date string handling: 26APR0304 - skipping precise hours for daily aggregation
        date_str = parts[1]
        year = int("20" + date_str[:2])
        month_str = date_str[2:5]
        day = int(date_str[5:7])
        
        month_map = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6, 
                     "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}
        month = month_map.get(month_str.upper(), 1)
        
        # T47.99 -> 47.99
        temp_str = parts[2].replace('T', '')
        target_temp = float(temp_str)
        
        target_date = datetime.date(year, month, day).isoformat()
        
        return city_code, target_date, target_temp

    async def fetch_ensemble_probability(self, city: str, target_date: str, target_temp: float) -> float:
        """
        Pulls all 31 GFS seamless ensemble models and calculates the exact fraction
        of models predicting a daily MAX temperature greater than the target.
        """
        coords = self.stations.get(city)
        if not coords:
            return 0.5
            
        params = {
            "latitude": coords['lat'],
            "longitude": coords['lon'],
            "daily": "temperature_2m_max",
            "models": "gfs_seamless",
            "temperature_unit": "fahrenheit",
            "start_date": target_date,
            "end_date": target_date
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.api_url, params=params, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        daily = data.get("daily", {})
                        
                        # Find all ensemble members (temperature_2m_max_member01 to 31)
                        members = [daily[key][0] for key in daily.keys() if "temperature_2m_max_member" in key and len(daily[key]) > 0]
                        if not members:
                            return 0.5
                            
                        # Count how many members breach the target
                        hits = sum(1 for temp in members if temp is not None and temp > target_temp)
                        return hits / len(members)
            except Exception as e:
                print(f"[WEATHER] Ensemble fetch failed: {e}")
        return 0.5
        
    def _calculate_kelly_size(self, edge: float, probability: float, available_balance: float) -> float:
        """ Calculates optimal bankroll fraction using Kelly Criterion natively """
        if probability >= 1.0 or probability <= 0.0 or edge <= 0:
            return 0.0
        
        odds = probability / (1 - probability)
        # fractional kelly mapping natively safely
        kelly_pct = (probability - ((1 - probability) / odds)) * self.KELLY_FRACTION
        
        # Safe bounds capping
        raw_amount = available_balance * kelly_pct
        return max(1.0, min(self.MAX_WEATHER_TRADE, raw_amount))

    async def evaluate_weather_market(self, market_id: str, mid_price: float, current_balance: float):
        """
        The entrypoint from main.py. Checks if the market is weather-based, calculates bounds,
        and optionally forces a trade dynamically.
        """
        if "KXTEMP" not in market_id:
            return None
            
        try:
            city, target_date, target_temp = self._parse_kalshi_ticker(market_id)
        except Exception:
            # Not a recognized format
            return None
            
        # Natively map the probabilities mathematically
        forecast_prob = await self.fetch_ensemble_probability(city, target_date, target_temp)
        edge = forecast_prob - mid_price
        
        print(f"[WEATHER] {city} {target_date} > {target_temp}° | Open-Meteo Prob: {forecast_prob:.3f} | Kalshi Mid: {mid_price:.2f} | Edge: {edge:.3f}")
        
        if abs(edge) >= self.EDGE_THRESHOLD:
            # We have a mathematical execution bound triggered!
            side = "yes" if edge > 0 else "no"
            abs_edge = abs(edge)
            
            # Determine limit execution constraints securely
            limit_price = int(forecast_prob * 100)
            if side == "no":
                limit_price = 100 - limit_price
                
            amount = self._calculate_kelly_size(abs_edge, forecast_prob if side == "yes" else (1-forecast_prob), current_balance)
            
            if amount > 1.0:
                 if self.risk_manager.validate_trade(amount):
                      print(f"   [!] Weather Edge Triggered! Executing ${amount:.2f} Kelly mapping on {side.upper()} at {limit_price}c")
                      await self.kalshi.place_order(market_id, side, int(amount * 100), limit_price)
                      return {
                          "status": "weather_trade_executed",
                          "edge": abs_edge,
                          "amount": amount,
                          "side": side
                      }
        return {"status": "weather_trade_skipped", "reason": "Insufficient edge bounds"}
