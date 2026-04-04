import time
from error_cache import error_cache

class MomentumRider:
    """
    Sub-agent deploying high-velocity trend following.
    Detects if a market is rocketing >6% inside brief windows and latches onto the momentum stream.
    """
    def __init__(self, kalshi_client, risk_manager):
        self.kalshi_client = kalshi_client
        self.risk_manager = risk_manager
        
        self.trailing_markets = {}
        # 0.8% micro-drift across 5-minutes (targets ~10-minute trade cadence)
        self.spike_threshold = 0.008
        self.time_window_seconds = 300
        self.unit_size_dollars = 5.0 # $5 per trade to stretch daily budget across 6x more trades
        
    async def evaluate_momentum(self, market_id: str, current_price: float):
        """
        Calculates trailing time constraints vs price acceleration.
        """
        current_time = time.time()
        
        if market_id not in self.trailing_markets:
            self.trailing_markets[market_id] = {
                "price": current_price, 
                "time": current_time,
                "highest_price": current_price
            }
            return {"status": "monitoring"}
            
        last_state = self.trailing_markets[market_id]
        time_elapsed = current_time - last_state["time"]
        price_drift = current_price - last_state["price"]
        
        # If the window expires and we don't hold an active order, reset the baseline
        if time_elapsed > self.time_window_seconds and not last_state.get("order_id"):
            self.trailing_markets[market_id] = {
                "price": current_price, 
                "time": current_time,
                "highest_price": current_price
            }
            return {"status": "monitoring"}
            
        # Is it a positive massive velocity spike?
        if price_drift >= self.spike_threshold:
            print(f"\n[MOMENTUM RIDER] 🚀 MASSIVE BREAKOUT ACCELERATION DETECTED ON {market_id}!")
            print(f"       -> Velocity: +{price_drift*100:.1f}% surge within {time_elapsed:.1f} seconds!")
            
            # Reset trailing baseline lock so we don't spam orders
            self.trailing_markets[market_id] = {"price": current_price, "time": current_time}
            
            if not self.risk_manager.validate_trade(self.unit_size_dollars):
                 print("[MOMENTUM RIDER] Global Risk limits vetoed momentum scaling.")
                 return {"status": "failed", "reason": "risk_limit"}
                 
            try:
                # MARKETEABLE LIMIT: Add +1 cent slippage to deliberately cross the spread and guarantee a fill!
                target_cents = min(99, int((current_price + 0.01) * 100))
                amount_cents = int(self.unit_size_dollars * 100)
                
                print(f"       -> Executing {amount_cents}c YES LIMIT lock @ {target_cents}c! (Includes +1c Sweep Slippage)")
                
                res = await self.kalshi_client.place_order(
                    market_id, "buy", amount_cents, target_cents
                )
                
                self.risk_manager.record_trade(self.unit_size_dollars)
                
                self.trailing_markets[market_id]["highest_price"] = current_price
                
                # Record the order_id so we can dump it if momentum reverses
                if res.get("status") == "simulated":
                    self.trailing_markets[market_id]["order_id"] = res.get("order_id")
                elif "order" in res.get("data", {}):
                    self.trailing_markets[market_id]["order_id"] = res["data"]["order"].get("order_id")
                    
                return {"status": "executed", "api_response": res}
            except Exception as e:
                error_cache.record_error("Momentum_Rider_Execution", e, {"market_id": market_id})
                return {"status": "error", "message": str(e)}
                
        # Is it collapsing? (Take profit / Trailing Stop Dump)
        order_locked = last_state.get("order_id")
        highest = last_state.get("highest_price", current_price)
        
        if current_price > highest:
            self.trailing_markets[market_id]["highest_price"] = current_price
            highest = current_price
            
        # Hard -2% reversal OR Trailing Stop Loss hits 2% down from the established peak!
        if price_drift <= -0.02 or (highest - current_price) >= 0.02:
             if order_locked:
                 print(f"[MOMENTUM RIDER] 📉 Trailing Stop Loss / Reversal hit (Peak {highest:.3f} | Curr {current_price:.3f}). Dumping exposure on {market_id}!")
                 await self.kalshi_client.cancel_order(order_locked)
                 
             self.trailing_markets[market_id] = {
                 "price": current_price, 
                 "time": current_time,
                 "highest_price": current_price
             }
             
        return {"status": "monitoring"}

    async def evaluate_momentum_imbalance(self, market_id: str, imbalance_ratio: float):
        """
        Triggered purely off of L2 Orderbook pressure prior to a price spike.
        """
        if imbalance_ratio >= 3.0:
            print(f"\n[L2 MOMENTUM RADAR] Intense Buy-side Book Weight Detected on {market_id}! ({imbalance_ratio:.1f}:1 B/A Ratio)")
            # Readying to fire. Logic here could prime the pipeline or reduce threshold latency locally.
