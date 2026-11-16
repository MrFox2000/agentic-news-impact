"""News providers.

`GoogleNewsSource` reads the public Google News RSS feed - no API key, no
signup. `FixtureNewsSource` returns the deterministic sample data instead, so
tests and offline demos stay hermetic.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Protocol

import feedparser
import httpx

from ..fixtures import sample_articles
from ..models import Article

GOOGLE_NEWS = "https://news.google.com/rss/search"
_TAG = re.compile(r"<[^>]+>")


class NewsSource(Protocol):
    async def search(self, query: str, days: int, limit: int) -> list[Article]: ...


def _article_id(url: str) -> str:
    return hashlib.blake2b(url.encode("utf-8"), digest_size=6).hexdigest()


def _published(entry) -> str:
    parsed = getattr(entry, "published_parsed", None)
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc).date().isoformat()
    return datetime.now(timezone.utc).date().isoformat()


class GoogleNewsSource:
    def __init__(self, timeout: float = 20.0) -> None:
        self._timeout = timeout

    async def search(self, query: str, days: int, limit: int) -> list[Article]:
        params = {
            "q": f"{query} when:{days}d",
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(GOOGLE_NEWS, params=params)
            response.raise_for_status()
            feed = feedparser.parse(response.text)

        articles: list[Article] = []
        seen: set[str] = set()
        for entry in feed.entries[: limit * 2]:
            url = getattr(entry, "link", "")
            title = _TAG.sub("", getattr(entry, "title", "")).strip()
            if not url or not title or url in seen:
                continue
            seen.add(url)
            source = getattr(entry, "source", None)
            origin = source.get("title") if isinstance(source, dict) else None
            articles.append(
                Article(
                    id=_article_id(url),
                    title=title,
                    source=(origin or "Google News").strip(),
                    url=url,
                    published=_published(entry),
                    summary=_TAG.sub("", getattr(entry, "summary", "")).strip()[:400],
                )
            )
            if len(articles) >= limit:
                break
        return articles


class FixtureNewsSource:
    async def search(self, query: str, days: int, limit: int) -> list[Article]:
        return sample_articles(query, days=days, limit=limit)


def build_news_source(settings) -> NewsSource:
    if settings.offline:
        return FixtureNewsSource()
    return GoogleNewsSource(timeout=settings.http_timeout)
