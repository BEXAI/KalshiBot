from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Kalshi Authentication
    KALSHI_API_KEY_ID: str = Field(..., description="Kalshi API Key ID")
    KALSHI_PRIVATE_KEY_PATH: str = Field(..., description="Absolute path to the Kalshi RSA .pem private key")
    KALSHI_API_URL: str = Field("https://api.elections.kalshi.com/trade-api/v2", description="Kalshi API endpoint (demo or prod)")
    KALSHI_ENV: str = Field("production", description="Kalshi environment: sandbox or production")
    # Trading Parameters
    PAPER_MODE: bool = Field(False, description="If True, routes to paper execution")
    MAX_TRADE_SIZE: float = Field(4.0, description="Max spend per trade in dollars/cents")
    MAX_DAILY_SPEND: float = Field(20.0, description="Max daily spend in dollars/cents")
    KILL_SWITCH_ACTIVE: bool = Field(False, description="Disable all trading if True")
    MAX_DRAWDOWN: float = Field(20.0, description="Max overall drawdown allowed")
    MIN_EDGE: float = Field(0.015, description="Minimum algorithmic edge difference (e.g. 0.015) needed to execute HFT triggers natively")
    
    # LLM Parameters
    OLLAMA_URL: str = Field("http://127.0.0.1:11434", description="Local Ollama instance URL")
    LLM_MODEL: str = Field("gemma4:31b", description="Local LLM model to use")
    GEMINI_API_KEY: str = Field("dummy_key", description="Google Gemini API Key for Lead Analyst fallback")
    
    # TimesFM Algorithmic Predictor Rules
    TIMESFM_ENABLED: bool = Field(True, description="Toggle Google TimesFM predictive analytics on or off")
    TIMESFM_MIN_HISTORY: int = Field(32, description="Minimum sequence length natively required for TimesFM zero-shot prediction")
    TIMESFM_MAX_HISTORY: int = Field(128, description="Maximum rolling buffer history before pruning natively")
    TIMESFM_HORIZON: int = Field(10, description="N-Ticks into the future that the model bounds natively")
    TIMESFM_COOLDOWN: int = Field(60, description="Cooldown natively to prevent model-exhaustion looping")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
