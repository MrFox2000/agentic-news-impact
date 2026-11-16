"""Deterministic sample data.

Used by the test suite and by `OFFLINE=1`, so the whole agent pipeline can run
with no network at all. The shapes match the real providers exactly, which is
what makes the rest of the code indifferent to where the data came from.
"""

from __future__ import annotations

from datetime import date, timedelta

from .models import Article, Bar

_HEADLINES = [
    ("{q} beats quarterly expectations as demand climbs", "Reuters"),
    ("Analysts raise {q} targets after strong guidance", "Bloomberg"),
    ("{q} slips as supply chain worries resurface", "CNBC"),
    ("Regulators open review into {q} practices", "Financial Times"),
    ("{q} announces expansion and new hiring round", "Reuters"),
    ("Short sellers increase bets against {q}", "MarketWatch"),
]

#: The synthetic series dips hard on days 4 and 9 of the window.
_SHOCKS = {4: -4.6, 9: 3.1, 14: -2.4}


def sample_articles(query: str, days: int = 30, limit: int = 25) -> list[Article]:
    today = date.today()
    articles: list[Article] = []
    for index, offset in enumerate([2, 3, 4, 8, 9, 13, 14, 20]):
        if offset > days:
            continue
        headline, source = _HEADLINES[index % len(_HEADLINES)]
        published = today - timedelta(days=offset)
        articles.append(
            Article(
                id=f"fixture-{index}",
                title=headline.format(q=query.upper()),
                source=source,
                url=f"https://example.com/{query.lower()}/{index}",
                published=published.isoformat(),
                summary=f"Sample article about {query.upper()} used in offline mode.",
            )
        )
    return articles[:limit]


def sample_bars(days: int = 30, base: float = 100.0) -> list[Bar]:
    today = date.today()
    bars: list[Bar] = []
    close = base
    for offset in range(days, 0, -1):
        day = today - timedelta(days=offset)
        if day.weekday() >= 5:  # skip weekends
            continue
        change = _SHOCKS.get(offset, 0.35)
        close = max(1.0, close * (1 + change / 100))
        bars.append(
            Bar(
                date=day.isoformat(),
                open=round(close * 0.995, 2),
                high=round(close * 1.01, 2),
                low=round(close * 0.985, 2),
                close=round(close, 2),
                volume=1_000_000 + offset * 1000,
            )
        )
    return bars
