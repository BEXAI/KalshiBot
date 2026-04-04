from error_cache import error_cache
from settings import settings

class MarketMaker:
    """
    Sub-agent deploying continuous dual-sided liquidity based on the Lead Analyst's probability deviation.
    """
    def __init__(self, kalshi_client, risk_manager):
         self.kalshi_client = kalshi_client
         self.risk_manager = risk_manager
         self.base_spread_cents = 3 # 3 cents symmetric spread
         self.max_inventory_dollars = settings.MAX_TRADE_SIZE
         self.active_limits = {}

    async def provide_liquidity(self, market_id: str, inferred_probability: float, active_mid_price: float = None):
         """
         Computes skew and executes dual rest orders around the AI true price.
         """
         if active_mid_price is None:
             # If exact mid-price isn't passed, default to falling back on inferred probability symmetric
             active_mid_price = inferred_probability

         # Asymmetric Skew Algorithm: Lean into AI Edge to capture favorable inventory
         ai_cents = int(inferred_probability * 100)
         mid_cents = int(active_mid_price * 100) if active_mid_price else ai_cents
         
         spread_cents = self.base_spread_cents
         if abs(inferred_probability - (active_mid_price or inferred_probability)) > 0.10:
             spread_cents = 8
             print(f"       -> [VOLATILITY PREMIUM] Extreme probability deviation. Baseline spread: {spread_cents}c")

         edge_cents = ai_cents - mid_cents
         
         if edge_cents > 2:
             # Market Undervalued: Bid aggressively tight, push ask far away
             optimal_bid_cents = ai_cents - 1
             optimal_ask_cents = ai_cents + spread_cents + edge_cents
         elif edge_cents < -2:
             # Market Overvalued: Ask aggressively tight, drop bid far away
             optimal_bid_cents = ai_cents - spread_cents + edge_cents
             optimal_ask_cents = ai_cents + 1
         else:
             optimal_bid_cents = ai_cents - spread_cents
             optimal_ask_cents = ai_cents + spread_cents
         
         # Boundary safety 
         optimal_bid_cents = max(1, min(98, optimal_bid_cents))
         optimal_ask_cents = max(2, min(99, optimal_ask_cents))
         
         if optimal_bid_cents >= optimal_ask_cents:
             print(f"[MARKET MAKER] Mathematical crossover anomaly detected on {market_id}. Skipping.")
             return {"status": "skipped", "reason": "spread_inverted"}
             
         trade_amount_cents = 500 # Defaults to 5 contracts ($5 risk per leg)

         if not self.risk_manager.validate_trade((trade_amount_cents * 2) / 100.0):
             return {"status": "skipped", "reason": "risk_manager_veto"}

         
         # QUEUE POSITION RETENTION: Only wipe orders if True Price drastically changes
         last_true_cents = self.active_limits.get(f"{market_id}_true_price")
         if last_true_cents is not None and abs(ai_cents - last_true_cents) <= 2:
             active_list = self.active_limits.get(market_id, [])
             if len(active_list) > 0:
                 print(f"       -> [QUEUE RETAINED] Keeping active limits. True price drift < 2c.")
                 return {"status": "retained", "reason": "drift_minimal"}

         print(f"\n[MARKET MAKER - {market_id}] Deploying Asymmetrical Liquidity Bounds!")
         print(f"       -> Target 'True Price': {inferred_probability:.2f}")
         print(f"       -> Quoting BID: {optimal_bid_cents}c | Quoting ASK: {optimal_ask_cents}c")

         # WIPE EXISTING TOXIC LIQUIDITY FIRST
         if market_id in self.active_limits and isinstance(self.active_limits[market_id], list):
             for order_id in self.active_limits[market_id]:
                 print(f"       -> [WIPE] Canceling Limit: {order_id}")
                 await self.kalshi_client.cancel_order(order_id)
             self.active_limits[market_id] = []
         else:
             self.active_limits[market_id] = []

         results = []
         try:
             # Submit hanging bid rest 
             bid_res = await self.kalshi_client.place_order(
                 market_id, "buy", trade_amount_cents, optimal_bid_cents
             )
             results.append({"bid_exec": bid_res})

             # Submit hanging ask rest (Selling YES is effectively Buying NO. Kalshi handles inverse.)
             ask_res = await self.kalshi_client.place_order(
                 market_id, "sell", trade_amount_cents, optimal_ask_cents
             )
             results.append({"ask_exec": ask_res})
             
             self.risk_manager.record_trade((trade_amount_cents * 2) / 100.0)
             
             new_limits = []
             for res in [bid_res, ask_res]:
                 if res.get("status") == "simulated":
                     new_limits.append(res["order_id"])
                 elif "order" in res.get("data", {}):
                     new_limits.append(res["data"]["order"].get("order_id"))
             self.active_limits[market_id] = new_limits
             self.active_limits[f"{market_id}_true_price"] = ai_cents

             
         except Exception as e:
             error_cache.record_error("Market_Maker_Execution", e, {"market_id": market_id})
             return {"status": "failed", "error": str(e)}
             
         return {
             "status": "liquidity_brackets_live",
             "mid": inferred_probability,
             "spread_quoted": [optimal_bid_cents, optimal_ask_cents],
             "responses": results
         }
