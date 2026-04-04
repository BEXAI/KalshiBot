import time
from error_cache import error_cache
from settings import settings

class CopyTrader:
    """
    Sub-agent mirroring profitable external wallets / accounts dynamically using Fractional Kelly Sizing.
    """
    def __init__(self, kalshi_client, risk_manager):
        self.kalshi_client = kalshi_client
        self.risk_manager = risk_manager
        
        # Fractional Kelly bounds
        self.kelly_fraction = 0.10 # We mimic external signals at exactly 10% of their velocity size
        
    async def execute_copy_trading_cycle(self, market_id: str, external_signals: list):
        """
        Parses whale trade webhooks and executes safe-bounded mirror limit orders.
        """
        # external_signals is typically injected via a Discord Webhook or Kalshi Leaderboard parse mechanism
        results = []
        for signal in external_signals:
            whale_size_dollars = signal.get("amount", 0.0)
            target_side = signal.get("action", "buy")
            target_limit = signal.get("price_cents", 50)
            
            # The Fractional Kelly Math restricts maximum mimicking safely inside Settings rules
            our_target_dollars = whale_size_dollars * self.kelly_fraction
            our_target_dollars = min(our_target_dollars, settings.MAX_TRADE_SIZE)
            
            if our_target_dollars < 1.0:
                print(f"[COPY TRADER] Signal from {signal.get('trader')} mathematically negligible.")
                continue
                
            if not self.risk_manager.validate_trade(our_target_dollars):
                print(f"[COPY TRADER] Risk Manager globally vetoed copy trade spanning ${our_target_dollars:.2f}")
                continue
                
            print(f"\n[COPY TRADER - FRACTIONAL KELLY] High Portfolio Velocity Signal Detected!")
            print(f"       -> Target {signal.get('trader')} executed ${whale_size_dollars:.2f} on {target_side.upper()} @ {target_limit}c.")
            print(f"       -> Scaling by {self.kelly_fraction*100}% -> Committing ${our_target_dollars:.2f} to clone execution.")
            
            try:
                res = await self.kalshi_client.place_order(
                    market_id, target_side, int(our_target_dollars * 100), target_limit
                )
                self.risk_manager.record_trade(our_target_dollars)
                results.append({"mimic_successful": True, "alloc": our_target_dollars, "rest_output": res})
                
            except Exception as e:
                error_cache.record_error("Copy_Trader_Execution", e, {"market": market_id})
                results.append({"mimic_successful": False, "error": str(e)})
                
        return results
