"""MCP server exposing the analysis tools.

Run it standalone:

    python -m app.mcp_server              # stdio
    python -m app.mcp_server --http 8765  # Streamable HTTP at http://127.0.0.1:8765/mcp

Any MCP host (Claude Desktop, an IDE, another agent) can then use these tools
without knowing anything about this repository.
"""

from __future__ import annotations

import argparse
import asyncio

from mcp.server import MCPServer

from .config import get_settings
from .sources.news import build_news_source
from .sources.prices import build_price_source
from .tools import ToolBox

_settings = get_settings()
_box = ToolBox(
    news=build_news_source(_settings),
    prices=build_price_source(_settings),
    threshold=_settings.move_threshold,
)

mcp = MCPServer("news-impact")


@mcp.tool()
async def search_news(query: str, days: int = 7, limit: int = 15) -> dict:
    """Search recent news headlines for a company, ticker or topic."""
    return await _box.search_news(query, days=days, limit=limit)


@mcp.tool()
async def price_history(symbol: str, days: int = 30) -> dict:
    """Daily closes for a ticker or crypto pair such as AAPL or BTC-USD."""
    return await _box.price_history(symbol, days=days)


@mcp.tool()
async def biggest_moves(symbol: str, days: int = 30, threshold: float = 2.0) -> dict:
    """Days where the close moved at least `threshold` percent."""
    return await _box.biggest_moves(symbol, days=days, threshold=threshold)


@mcp.tool()
async def correlate(symbol: str, query: str, days: int = 30, lookback: int = 2) -> dict:
    """Pair each large price move with the headlines published just before it."""
    return await _box.correlate(symbol, query, days=days, lookback=lookback)


def main() -> None:
    parser = argparse.ArgumentParser(description="news-impact MCP server")
    parser.add_argument("--http", type=int, default=None, help="serve Streamable HTTP on this port")
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=args.http)
    else:
        asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
