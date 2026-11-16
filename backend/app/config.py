"""Application settings."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Agentic News Impact"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    openai_api_key: str | None = None
    chat_model: str = "gpt-4o-mini"

    #: When set, the agent talks to a real MCP server over Streamable HTTP.
    mcp_url: str | None = None
    #: When true, all network calls are served from committed fixtures.
    offline: bool = False

    http_timeout: float = 20.0
    max_news: int = 25
    default_days: int = 30
    move_threshold: float = 2.0

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def can_generate(self) -> bool:
        """True when an LLM is available for free-form synthesis."""
        return bool(self.openai_api_key) and not self.offline


@lru_cache
def get_settings() -> Settings:
    return Settings(offline=os.getenv("OFFLINE", "").lower() in {"1", "true", "yes"})
