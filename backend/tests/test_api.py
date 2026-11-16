from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def events(text: str) -> list[dict]:
    return [
        json.loads(line[len("data: ") :])
        for line in text.splitlines()
        if line.startswith("data: ")
    ]


def test_health_reports_mcp_mode(client: TestClient) -> None:
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["agent_mode"] == "in-process-mcp"
    assert body["offline_data"] is True


def test_tools_are_listed_through_mcp(client: TestClient) -> None:
    tools = client.get("/api/tools").json()

    assert len(tools) == 4
    assert {tool["name"] for tool in tools} == {
        "search_news",
        "price_history",
        "biggest_moves",
        "correlate",
    }
    assert all(tool["description"] for tool in tools)


def test_analyze_streams_steps_then_report(client: TestClient) -> None:
    response = client.post("/api/analyze", json={"symbol": "AAPL", "question": "Apple", "days": 30})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    frames = events(response.text)
    kinds = [frame["type"] for frame in frames]

    assert kinds[0] == "step"
    assert kinds[-1] == "done"
    assert "report" in kinds
    assert kinds.index("report") < kinds.index("done")

    steps = [frame["node"] for frame in frames if frame["type"] == "step"]
    assert steps == ["plan", "collect", "report"]

    report = next(frame["markdown"] for frame in frames if frame["type"] == "report")
    assert "AAPL" in report
    assert "correlation" in report.lower()


def test_analyze_rejects_blank_symbol(client: TestClient) -> None:
    response = client.post("/api/analyze", json={"symbol": ""})

    assert response.status_code == 422


def test_analyze_rejects_absurd_window(client: TestClient) -> None:
    response = client.post("/api/analyze", json={"symbol": "AAPL", "days": 5000})

    assert response.status_code == 422
