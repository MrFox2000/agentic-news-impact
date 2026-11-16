"""The MCP server is tested over a real client session, not by calling functions."""

from __future__ import annotations

import asyncio

from mcp import Client

from app.mcp_server import mcp

EXPECTED = ["biggest_moves", "correlate", "price_history", "search_news"]


def run(coroutine):
    return asyncio.run(coroutine)


from app.mcp_client import unpack as collect


def test_server_advertises_its_tools() -> None:
    async def call():
        async with Client(mcp) as client:
            return await client.list_tools()

    listed = run(call())

    assert sorted(tool.name for tool in listed.tools) == EXPECTED
    assert all(tool.description for tool in listed.tools)


def test_price_history_returns_bars() -> None:
    async def call():
        async with Client(mcp) as client:
            return await client.call_tool("price_history", {"symbol": "AAPL", "days": 10})

    payload = collect(run(call()))

    assert payload["symbol"] == "AAPL"
    assert payload["count"] > 0
    assert payload["summary"]["bars"] > 0


def test_search_news_returns_articles() -> None:
    async def call():
        async with Client(mcp) as client:
            return await client.call_tool("search_news", {"query": "Tesla", "days": 30})

    payload = collect(run(call()))

    assert payload["count"] > 0
    assert {"title", "source", "url", "published"} <= set(payload["articles"][0])


def test_correlate_pairs_moves_with_headlines() -> None:
    async def call():
        async with Client(mcp) as client:
            return await client.call_tool(
                "correlate", {"symbol": "AAPL", "query": "Apple", "days": 30}
            )

    payload = collect(run(call()))

    assert payload["impacts"], "the fixture series has large moves in it"
    assert payload["summary"]["bars"] > 0
    assert "articles" in payload["impacts"][0]


def test_biggest_moves_respects_threshold() -> None:
    async def call(threshold: float):
        async with Client(mcp) as client:
            return await client.call_tool(
                "biggest_moves", {"symbol": "AAPL", "days": 30, "threshold": threshold}
            )

    loose = collect(run(call(0.5)))
    strict = collect(run(call(6.0)))

    assert len(loose["moves"]) >= len(strict["moves"])
    assert all(abs(move["change_pct"]) >= 6.0 for move in strict["moves"])

