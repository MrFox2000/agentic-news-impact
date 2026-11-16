"""Shared data shapes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    source: str
    url: str
    published: str  # ISO date, UTC
    summary: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published": self.published,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def as_dict(self) -> dict[str, float | str]:
        return {
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass(frozen=True)
class Move:
    date: str
    close: float
    change_pct: float

    def as_dict(self) -> dict[str, float | str]:
        return {"date": self.date, "close": self.close, "change_pct": self.change_pct}


@dataclass
class Impact:
    """A price move with the articles published just before it."""

    move: Move
    articles: list[Article] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "move": self.move.as_dict(),
            "articles": [article.as_dict() for article in self.articles],
        }
