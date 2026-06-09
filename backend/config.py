from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_PLACEHOLDER_MARKERS = (
    "your-",
    "sk-your",
    "tvly-your",
    "your-project",
    "...",
)


def _env_file_paths() -> tuple[str, ...]:
    """Load repo-root .env first, then backend/.env (later files override)."""
    paths = (_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env")
    existing = tuple(str(p) for p in paths if p.exists())
    return existing or (str(_BACKEND_DIR / ".env"),)


def is_configured_value(value: Optional[str]) -> bool:
    """Return True when an env value is non-empty and not an example placeholder."""
    if not value or not value.strip():
        return False
    lowered = value.strip().lower()
    return not any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


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

    # Tavily Search API (optional; DuckDuckGo is used as fallback)
    TAVILY_API_KEY: Optional[str] = None

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # Backend server
    BACKEND_PORT: int = 8000
    BACKEND_HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:3000"

    # Default model
    MODEL: str = "deepseek-chat"

    # Research pipeline controls
    MAX_TOPIC_LENGTH: int = 500
    SEARCH_MAX_RESULTS: int = 5
    FETCH_TOP_N: int = 3
    MAX_PARALLEL_RESEARCH_TASKS: int = 4
    CONTENT_FETCH_TIMEOUT_SECONDS: float = 10.0
    CONTENT_FETCH_MAX_CHARS: int = 5000
    REQUIRE_LLM_FOR_RESEARCH: bool = False

    # Report storage directory
    REPORTS_DIR: str = str(_BACKEND_DIR / "reports")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def active_model(self) -> str:
        if self.LLM_PROVIDER.lower() == "anthropic":
            return self.ANTHROPIC_MODEL
        return self.MODEL

    @property
    def llm_configured(self) -> bool:
        if self.LLM_PROVIDER.lower() == "anthropic":
            return is_configured_value(self.ANTHROPIC_API_KEY)
        return is_configured_value(self.DEEPSEEK_API_KEY)

    @property
    def tavily_configured(self) -> bool:
        return is_configured_value(self.TAVILY_API_KEY)

    @property
    def supabase_configured(self) -> bool:
        return (
            is_configured_value(self.SUPABASE_URL)
            and is_configured_value(self.SUPABASE_ANON_KEY)
        )

    model_config = {
        "env_file": _env_file_paths(),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


config = Config()
