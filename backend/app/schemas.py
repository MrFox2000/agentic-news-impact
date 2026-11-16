"""Request and response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16, description="Ticker or crypto pair")
    question: str = Field(default="", max_length=300, description="Optional focus")
    days: int | None = Field(default=None, ge=7, le=365)


class ToolInfo(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
