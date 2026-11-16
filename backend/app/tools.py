"""The tools the agent can call.

Every tool returns plain JSON-serialisable data, because the exact same
functions are exposed over the Model Context Protocol from `mcp_server.py` and
called directly in offline mode. One implementation, two transports.
"""

from __future__ import annotations

from dataclasses import dataclass

from .analysis import align, biggest_moves, summarise
from .sources.news import NewsSource
from .sources.prices import PriceSource


@dataclass
class ToolBox:
    news: NewsSource
    prices: PriceSource
    threshold: float = 2.0

    async def search_news(self, query: str, days: int = 7, limit: int = 15) -> dict:
        """Search recent news headlines for a company, ticker or topic."""
        articles = await self.news.search(query, days=days, limit=limit)
        return {
            "query": query,
            "days": days,
            "count": len(articles),
            "articles": [article.as_dict() for article in articles],
        }

    async def price_history(self, symbol: str, days: int = 30) -> dict:
        """Daily closes for a ticker or crypto pair, e.g. AAPL or BTC-USD."""
        bars = await self.prices.history(symbol, days=days)
        return {
            "symbol": symbol.upper(),
            "count": len(bars),
            "summary": summarise(bars),
            "bars": [bar.as_dict() for bar in bars],
        }

    async def biggest_moves(self, symbol: str, days: int = 30, threshold: float | None = None) -> dict:
        """Days where the close moved at least `threshold` percent."""
        bars = await self.prices.history(symbol, days=days)
        cut = self.threshold if threshold is None else threshold
        moves = biggest_moves(bars, threshold=cut)
        return {
            "symbol": symbol.upper(),
            "threshold_pct": cut,
            "moves": [move.as_dict() for move in moves],
        }

    async def correlate(self, symbol: str, query: str, days: int = 30, lookback: int = 2) -> dict:
        """Pair each large price move with the headlines published just before it."""
        bars = await self.prices.history(symbol, days=days)
        articles = await self.news.search(query or symbol, days=max(days, 7), limit=40)
        moves = biggest_moves(bars, threshold=self.threshold)
        impacts = align(articles, moves, lookback=lookback)
        return {
            "symbol": symbol.upper(),
            "query": query,
            "window_days": days,
            "summary": summarise(bars),
            "impacts": [impact.as_dict() for impact in impacts],
        }


#: Names shown to the model and to the UI.
TOOL_SPECS = [
    {
        "name": "search_news",
        "description": "Search recent news headlines for a company, ticker or topic.",
        "args": {"query": "str", "days": "int", "limit": "int"},
    },
    {
        "name": "price_history",
        "description": "Daily closes for a ticker or crypto pair such as AAPL or BTC-USD.",
        "args": {"symbol": "str", "days": "int"},
    },
    {
        "name": "biggest_moves",
        "description": "Days where the close moved at least a threshold percent.",
        "args": {"symbol": "str", "days": "int", "threshold": "float"},
    },
    {
        "name": "correlate",
        "description": "Pair each large price move with headlines published just before it.",
        "args": {"symbol": "str", "query": "str", "days": "int", "lookback": "int"},
    },
]
