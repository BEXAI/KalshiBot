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
    
    # LLM Parameters
    OLLAMA_URL: str = Field("http://localhost:11434", description="Local Ollama instance URL")
    LLM_MODEL: str = Field("gemma4:31b", description="Local LLM model to use")
    GEMINI_API_KEY: str = Field("dummy_key", description="Google Gemini API Key for Lead Analyst fallback")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
