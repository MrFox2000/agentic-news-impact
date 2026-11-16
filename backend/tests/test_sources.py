from __future__ import annotations

import pytest

from app.sources.prices import (
    coin_id,
    is_crypto,
    parse_coingecko,
    parse_yahoo_chart,
)


def yahoo_payload(closes: list[float | None], stamps: list[int]) -> dict:
    return {
        "chart": {
            "result": [
                {
                    "timestamp": stamps,
                    "indicators": {
                        "quote": [
                            {
                                "open": closes,
                                "high": closes,
                                "low": closes,
                                "close": closes,
                                "volume": [1000] * len(closes),
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


def test_parse_yahoo_chart_builds_daily_bars() -> None:
    payload = yahoo_payload([10.0, 11.5], [1772150400, 1772236800])

    bars = parse_yahoo_chart(payload)

    assert len(bars) == 2
    assert bars[0].close == 10.0
    assert bars[1].close == 11.5
    assert bars[0].date == "2026-02-27"


def test_parse_yahoo_chart_skips_missing_closes() -> None:
    payload = yahoo_payload([10.0, None, 12.0], [1772150400, 1772236800, 1772323200])

    bars = parse_yahoo_chart(payload)

    assert [bar.close for bar in bars] == [10.0, 12.0]


def test_parse_yahoo_chart_tolerates_empty_response() -> None:
    assert parse_yahoo_chart({"chart": {"result": [], "error": "Not found"}}) == []


def test_parse_coingecko_extracts_prices() -> None:
    payload = {"prices": [[1772150400000, 64000.5], [1772236800000, 65100.0]]}

    bars = parse_coingecko(payload)

    assert len(bars) == 2
    assert bars[1].close == 65100.0


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [("BTC-USD", True), ("ETH", True), ("btc", True), ("AAPL", False), ("^GSPC", False)],
)
def test_is_crypto(symbol: str, expected: bool) -> None:
    assert is_crypto(symbol) is expected


def test_coin_id_maps_known_symbols() -> None:
    assert coin_id("BTC-USD") == "bitcoin"
    assert coin_id("SOL") == "solana"
