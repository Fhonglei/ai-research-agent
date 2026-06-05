from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent


def _env_file_paths() -> tuple[str, ...]:
    """Load repo-root .env first, then backend/.env (later files override)."""
    paths = (_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env")
    existing = tuple(str(p) for p in paths if p.exists())
    return existing or (str(_BACKEND_DIR / ".env"),)


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    # LLM provider: deepseek (OpenAI-compatible) or anthropic
    LLM_PROVIDER: str = "deepseek"

    # DeepSeek API (OpenAI-compatible)
    DEEPSEEK_API_KEY: Optional[str] = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # Anthropic API (optional)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-opus-4-8"

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

    @property
    def active_model(self) -> str:
        if self.LLM_PROVIDER.lower() == "anthropic":
            return self.ANTHROPIC_MODEL
        return self.MODEL

    # Report storage directory
    REPORTS_DIR: str = "reports"

    model_config = {
        "env_file": _env_file_paths(),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


config = Config()
