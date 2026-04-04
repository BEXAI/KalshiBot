from datetime import date
from settings import settings

class RiskManager:
    """
    Independent guardrails to track and validate sizes before placing limits orders.
    """
    def __init__(self):
        self.max_trade_size = settings.MAX_TRADE_SIZE
        self.max_daily_spend = settings.MAX_DAILY_SPEND
        self.kill_switch = settings.KILL_SWITCH_ACTIVE
        self.max_drawdown = settings.MAX_DRAWDOWN
        self.paper_mode = settings.PAPER_MODE
        
        # State tracking (would normally be persistent)
        self.current_daily_spend = 0.0
        self.current_drawdown = 0.0
        self.last_trade_date = date.today()

    def validate_trade(self, amount: float) -> bool:
        """
        Validates if the requested trade amount passes risk constraints.
        """
        today_date = date.today()
        if self.last_trade_date != today_date:
            self.current_daily_spend = 0.0
            self.last_trade_date = today_date

        if self.kill_switch:
            print("Risk Check Failed: KILL_SWITCH is ACTIVE.")
            return False

        if amount > self.max_trade_size:
            print(f"Risk Check Failed: Order size {amount} exceeds MAX_TRADE_SIZE {self.max_trade_size}")
            return False

        if self.current_daily_spend + amount > self.max_daily_spend:
            print("Risk Check Failed: Daily spend limit reached.")
            return False
            
        if self.current_drawdown > self.max_drawdown:
            print("Risk Check Failed: Max drawdown limit breached.")
            return False

        return True

    def record_trade(self, amount: float):
        """
        Records the executed trade amount to current limits.
        """
        self.current_daily_spend += amount
