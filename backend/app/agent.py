"""The agent.

A small LangGraph state machine that plans, calls MCP tools, and writes a
report. Tools are reached through a real MCP client, so the same graph works
against an in-process server (tests) or a remote one over Streamable HTTP.
"""

from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from mcp import Client

from .config import Settings
from .mcp_client import call_tool


class AgentState(TypedDict, total=False):
    symbol: str
    question: str
    days: int
    query: str
    impacts: dict[str, Any]
    steps: list[dict[str, str]]
    report: str
    error: str


def _step(node: str, detail: str) -> dict[str, str]:
    return {"node": node, "detail": detail}


def build_graph(tool_target: Any, settings: Settings):
    """Compile the plan -> collect -> report graph.

    `tool_target` is anything `mcp.Client` accepts: an `MCPServer` instance or a
    URL string such as "http://127.0.0.1:8765/mcp".
    """

    async def plan(state: AgentState) -> dict[str, Any]:
        symbol = state["symbol"].strip().upper()
        days = int(state.get("days") or settings.default_days)
        question = (state.get("question") or "").strip()
        query = question or symbol
        return {
            "symbol": symbol,
            "days": days,
            "query": query,
            "steps": [_step("plan", f"Investigate {symbol} over the last {days} days")],
        }

    async def collect(state: AgentState) -> dict[str, Any]:
        payload = await call_tool(
            tool_target,
            "correlate",
            {
                "symbol": state["symbol"],
                "query": state["query"],
                "days": state["days"],
                "lookback": 2,
            },
        )
        impacts = payload.get("impacts", [])
        summary = payload.get("summary", {})
        detail = (
            f"Pulled {summary.get('bars', 0)} daily bars "
            f"({summary.get('first_date')} to {summary.get('last_date')}) and matched "
            f"{len(impacts)} large moves against the news"
        )
        steps = list(state.get("steps", [])) + [_step("collect", detail)]
        return {"impacts": payload, "steps": steps}

    async def report(state: AgentState) -> dict[str, Any]:
        payload = state.get("impacts", {})
        text = await _write_report(payload, settings)
        steps = list(state.get("steps", [])) + [
            _step("report", "Wrote the impact report")
        ]
        return {"report": text, "steps": steps}

    graph = StateGraph(AgentState)
    graph.add_node("plan", plan)
    graph.add_node("collect", collect)
    graph.add_node("report", report)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "collect")
    graph.add_edge("collect", "report")
    graph.add_edge("report", END)
    return graph.compile()


def _render_template(payload: dict[str, Any]) -> str:
    """Deterministic report, used when no LLM is configured."""
    symbol = payload.get("symbol", "?")
    summary = payload.get("summary") or {}
    impacts = payload.get("impacts") or []

    lines = [
        f"## {symbol} — news and price moves",
        "",
        f"Window: {summary.get('first_date', '?')} to {summary.get('last_date', '?')}, "
        f"{summary.get('change_pct', 0)}% overall "
        f"(close {summary.get('first_close', '?')} → {summary.get('last_close', '?')}).",
        "",
    ]

    if not impacts:
        lines.append("No single day moved far enough to stand out in this window.")
        return "\n".join(lines)

    for entry in impacts:
        move = entry["move"]
        direction = "fell" if move["change_pct"] < 0 else "rose"
        lines.append(
            f"### {move['date']} — {symbol} {direction} {abs(move['change_pct'])}% "
            f"to {move['close']}"
        )
        articles = entry.get("articles") or []
        if not articles:
            lines.append("")
            lines.append("No headlines in the two days before this move.")
            lines.append("")
            continue
        for article in articles:
            lines.append(
                f"- {article['published']} · {article['source']} — "
                f"[{article['title']}]({article['url']})"
            )
        lines.append("")

    lines.append(
        "> These are headlines published shortly before each move. That is "
        "correlation, not proof of cause."
    )
    return "\n".join(lines)


async def _write_report(payload: dict[str, Any], settings: Settings) -> str:
    if not settings.can_generate:
        return _render_template(payload)

    from langchain_openai import ChatOpenAI

    trimmed = {
        "symbol": payload.get("symbol"),
        "summary": payload.get("summary"),
        "impacts": [
            {
                "date": entry["move"]["date"],
                "change_pct": entry["move"]["change_pct"],
                "close": entry["move"]["close"],
                "articles": [
                    {
                        "published": article["published"],
                        "source": article["source"],
                        "title": article["title"],
                        "url": article["url"],
                    }
                    for article in entry.get("articles", [])
                ],
            }
            for entry in payload.get("impacts", [])
        ],
    }

    model = ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )
    prompt = (
        "You are a market research assistant. Using ONLY the JSON data below, write a "
        "short markdown report in English.\n"
        "Structure: one-line summary, then a section per large move with the date and "
        "percentage, then the headlines published in the two days before it as links.\n"
        "State plainly that this is correlation, not causation. Do not invent numbers "
        "or headlines that are not in the data.\n\n"
        f"```json\n{json.dumps(trimmed, ensure_ascii=False)}\n```"
    )
    response = await model.ainvoke(prompt)
    content = response.content
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") for block in content if isinstance(block, dict)
    )
