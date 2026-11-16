"""FastAPI surface: one streaming endpoint plus MCP introspection."""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from mcp import Client

from .agent import build_graph
from .config import get_settings
from .mcp_server import mcp as inprocess_server
from .schemas import AnalyzeRequest, ToolInfo

settings = get_settings()

#: Every tool call goes through a real MCP session - in-process here, remote when
#: MCP_URL is set.
tool_target = settings.mcp_url or inprocess_server
graph = build_graph(tool_target, settings)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "An agent that reads the news and checks what the price did afterwards. "
        "Tools are served over the Model Context Protocol."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


async def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "agent_mode": "remote-mcp" if settings.mcp_url else "in-process-mcp",
        "llm": settings.can_generate,
        "offline_data": settings.offline,
    }


@app.get("/api/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    """The tools exactly as the MCP server advertises them."""
    async with Client(tool_target) as client:
        listed = await client.list_tools()
    return [
        ToolInfo(
            name=tool.name,
            description=(tool.description or "").strip(),
            input_schema=getattr(tool, "input_schema", None) or {},
        )
        for tool in listed.tools
    ]


async def _run(request: AnalyzeRequest) -> AsyncIterator[str]:
    initial = {
        "symbol": request.symbol,
        "question": request.question,
        "days": request.days or settings.default_days,
    }
    seen = 0
    try:
        async for chunk in graph.astream(initial, stream_mode="updates"):
            for node, update in chunk.items():
                if not isinstance(update, dict):
                    continue
                steps = update.get("steps") or []
                while seen < len(steps):
                    yield await _sse({"type": "step", **steps[seen]})
                    seen += 1
                if update.get("report"):
                    yield await _sse({"type": "report", "markdown": update["report"]})
    except Exception as exc:  # pragma: no cover - network dependent
        yield await _sse({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
    yield await _sse({"type": "done"})


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest) -> StreamingResponse:
    if not request.symbol.strip():
        raise HTTPException(status_code=422, detail="symbol is required")

    return StreamingResponse(
        _run(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
