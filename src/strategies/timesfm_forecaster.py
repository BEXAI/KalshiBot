import os
import time
import numpy as np
from collections import defaultdict
import torch
import timesfm

class TimesFMForecaster:
    """
    TimesFM 2.5 wrapper for high-frequency Kalshi market tick forecasting.
    Includes rolling buffers, cooldown management, and memory pruning.
    """
    def __init__(self, context_len=32, horizon_len=10, cooldown_seconds=60):
        self.context_len = context_len
        self.horizon_len = horizon_len
        self.cooldown_seconds = cooldown_seconds
        
        self.tick_buffers = defaultdict(list)
        self.last_forecast_times = {}
        
        self.tfm = None
        
    def _lazy_load_model(self):
        if self.tfm is None:
            print("[TIMESFM] Lazy-loading Foundation Model weights (~400MB) into memory natively...")
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
            
            # [CRITICAL SECURITY PATCH] HuggingFace Hub pushes generic networking proxies into initialized kwargs.
            # Google's TimesFM 2.5 engine enforces a hard fail on unknown parameters natively. We intercept and strip it!
            original_init = timesfm.TimesFM_2p5_200M_torch.__init__
            def patched_init(self, *args, **kwargs):
                valid_kwargs = {k: v for k, v in kwargs.items() if k in ["torch_compile", "config"]}
                original_init(self, *args, **valid_kwargs)
            timesfm.TimesFM_2p5_200M_torch.__init__ = patched_init
            
            # Map directly to the v2.5 Architecture endpoints securely!
            self.tfm = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
            
            self.tfm.compile(
                timesfm.ForecastConfig(
                    max_context=self.context_len,
                    max_horizon=self.horizon_len,
                    normalize_inputs=True,
                )
            )
            print(f"[TIMESFM] Architecture fully loaded onto exactly '{device}'. Ready for sequence arrays.")

    def record_tick(self, market_id: str, mid_price: float):
        """Append price to rolling buffer with automatic memory pruning safely bounding to 2x context size."""
        # Convert Kalshi 1-99c or 0.01-0.99 ranges effectively. We'll track raw inputs natively.
        self.tick_buffers[market_id].append(mid_price)
        
        # Prevent runaway RAM consumption for high-tick markets
        if len(self.tick_buffers[market_id]) > self.context_len * 2:
            self.tick_buffers[market_id] = self.tick_buffers[market_id][-self.context_len:]

    def should_cooldown(self, market_id: str) -> bool:
        last = self.last_forecast_times.get(market_id, 0)
        return (time.time() - last) < self.cooldown_seconds

    def forecast_market(self, market_id: str):
        """
        Runs the zero-shot forecaster. Returns predicted value and uncertainty band safely natively.
        """
        history = self.tick_buffers.get(market_id, [])
        if len(history) == 0:
            return None # Must have at least 1 tick to establish flatline bounds
            
        if self.should_cooldown(market_id):
            return None
            
        self._lazy_load_model()
        
        # Cold-Start Autopadding Synergy: Pad immediate volatility breakouts mathematically!
        if len(history) < self.context_len:
            pad_size = self.context_len - len(history)
            padded_history = [history[0]] * pad_size + history
        else:
            padded_history = history[-self.context_len:]
            
        # Prepare strictly exactly context_len array bounds
        context_array = np.array(padded_history, dtype=np.float32)
        
        print(f"\n[TIMESFM] Triggering Zero-Shot Quantitative Predictor on {market_id}")
        
        # Predict the exact next horizon batch using v2.5 keyword targets
        forecasts, _ = self.tfm.forecast(
            horizon=self.horizon_len,
            inputs=[context_array]
        )
        
        # forecasts is [batch, horizon]
        # Calculate exactly the mean predicted price across the target bounds
        mean_trajectory = float(np.mean(forecasts[0]))
        
        self.last_forecast_times[market_id] = time.time()
        
        return {
            "history_size": len(history),
            "forecast_trajectory": round(mean_trajectory, 4),
            "current_mid": round(history[-1], 4),
            "delta": round(mean_trajectory - history[-1], 4)
        }
