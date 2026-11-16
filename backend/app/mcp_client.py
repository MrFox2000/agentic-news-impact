"""Thin MCP client helper.

Tool results arrive either as `structured_content` or as a JSON string inside a
text content block, depending on whether the tool declares an output schema.
Both shapes are normalised to a plain dict here so callers never care.
"""

from __future__ import annotations

import json
from typing import Any

from mcp import Client


def unpack(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structured_content", None)
    if structured:
        if set(structured) == {"result"} and isinstance(structured["result"], dict):
            return structured["result"]
        return structured

    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(payload, dict):
            return payload

    return {}


async def call_tool(target: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Open an MCP session, call one tool, close the session."""
    async with Client(target) as client:
        result = await client.call_tool(name, arguments)
    return unpack(result)


async def list_tools(target: Any) -> list[Any]:
    async with Client(target) as client:
        listed = await client.list_tools()
    return list(listed.tools)
