from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    # DeepSeek API (OpenAI-compatible)
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # Tavily Search API (optional — DuckDuckGo used as fallback)
    TAVILY_API_KEY: Optional[str] = None

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # Backend server
    BACKEND_PORT: int = 8000
    BACKEND_HOST: str = "0.0.0.0"

    # Default model
    MODEL: str = "deepseek-chat"

    # Report storage directory
    REPORTS_DIR: str = "reports"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


config = Config()
