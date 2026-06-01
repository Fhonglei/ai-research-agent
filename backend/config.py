from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Anthropic API
    ANTHROPIC_API_KEY: str

    # Tavily Search API
    TAVILY_API_KEY: str

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # Backend server
    BACKEND_PORT: int = 8000
    BACKEND_HOST: str = "0.0.0.0"

    # Default Claude model
    MODEL: str = "claude-sonnet-4-6"

    # Report storage directory
    REPORTS_DIR: str = "reports"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


config = Config()
