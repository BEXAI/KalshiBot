import re
import time

class TickAggregator:
    """
    A lightweight state engine that prevents sending every single micro-tick
    across the websocket into our LLM debate engine.
    """
    def __init__(self, threshold: float = 0.002):
        self.market_states = {}
        # The delta variance necessary to trigger an AI evaluation (e.g., 0.2% drift)
        self.threshold = threshold

        # Strategic Ticker Regex Filter
        # Covers Crypto, Politics, Macro, Energy, Weather, and major index markets
        self.whitelist_pattern = re.compile(r'^(BTC|ETH|POL|FED|CPI|ELECTION|KXBTC|KXETH|KXSP|KXDOW|KXNFP|KXGDP|KXINX|KXTEMP|KXGAS|INX|SP500|NASDAQ|DOW|GDP|NFP|RATE|TRUMP|HARRIS|TARIFF)-', re.IGNORECASE)

        # Time-based evaluation floor: force AI eval even if price hasn't drifted
        self.last_trigger_times = {}
        self.time_floor_seconds = 30  # 30 seconds to force ultra-fast execution
        self._last_prune = time.time()

    def is_strategic_market(self, market_id: str) -> bool:
        """Determines if the market belongs to an active category. For MVP deployment, we track all Kalshi prefix markets to guarantee rapid baseline execution bounds."""
        return "KX" in market_id.upper()

    def is_toxic_market(self, market_title: str) -> bool:
        """
        Rejects Multi-Leg Combos and Parlay Markets which destroy standard single-variable AI Inference assumptions.
        """
        title_norm = market_title.lower()
        toxic_keywords = ["combo", "leg", "parlay", "multi-game"]
        for kw in toxic_keywords:
            if kw in title_norm:
                return True
        return False

    def is_profitable_bounds(self, current_price: float) -> bool:
        """
        Rejects extreme longshots (< 10c) and extreme sure-things (> 90c).
        Optimizes heavy compute parameters and balances capital ROI.
        """
        return 0.10 <= current_price <= 0.90

    def should_trigger_ai(self, market_id: str, current_price: float) -> bool:
        now = time.time()
        
        # Memory Optimization: Prune stale markets every 60 minutes
        if now - getattr(self, '_last_prune', 0) > 3600:
            self._last_prune = now
            stale_keys = [k for k, v in self.last_trigger_times.items() if now - v > 7200]
            for k in stale_keys:
                self.last_trigger_times.pop(k, None)
                self.market_states.pop(k, None)

        if market_id not in self.market_states:
            self.market_states[market_id] = current_price
            self.last_trigger_times[market_id] = now
            return True

        last_evaluated_price = self.market_states[market_id]
        drift = abs(current_price - last_evaluated_price)

        # Time-based floor: force evaluation if 10 minutes have elapsed
        time_since_last = now - self.last_trigger_times.get(market_id, 0)
        time_triggered = time_since_last >= self.time_floor_seconds

        if drift >= self.threshold or time_triggered:
            reason = f"Variance {drift:.4f}" if drift >= self.threshold else f"Time floor {time_since_last:.0f}s"
            print(f"[{market_id}] AI trigger: {reason}. Updating cached baseline.")
            self.market_states[market_id] = current_price
            self.last_trigger_times[market_id] = now
            return True

        return False

    def track_orderbook(self, market_id: str, ob_data: dict) -> float:
        """
        Calculates resting limit order book imbalance to predict momentum before it happens.
        Returns the ratio of Bids/Asks volume mapped to Kalshi's L2 `orderbook_delta` schema.
        """
        bids = ob_data.get("bids", [])
        asks = ob_data.get("asks", [])
        
        bid_vol = sum(int(q) for p, q in bids)
        ask_vol = sum(int(q) for p, q in asks)
        
        if ask_vol == 0 and bid_vol > 0:
            return 999.0 # Max Imbalance
        if ask_vol == 0:
             return 1.0 # Neutral if empty
             
        ratio = bid_vol / ask_vol
        return ratio
