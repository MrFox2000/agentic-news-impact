"""Price providers.

Yahoo Finance's chart endpoint is used for everything: it needs no key, covers
equities (`AAPL`), indices (`^GSPC`) and crypto pairs (`BTC-USD`) with the same
response shape, and it is the only free source currently reachable from here.
CoinGecko is kept as a fallback for crypto if Yahoo rate-limits.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from typing import Protocol

import httpx

from ..fixtures import sample_bars
from ..models import Bar

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
COINGECKO_CHART = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
UA = {"User-Agent": "Mozilla/5.0 (compatible; agentic-news-impact/0.1)"}

COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "BNB": "binancecoin",
    "AVAX": "avalanche-2",
    "TON": "the-open-network",
    "LINK": "chainlink",
}

_CACHE: dict[str, tuple[float, list[Bar]]] = {}
_CACHE_TTL = 300.0


class PriceSource(Protocol):
    async def history(self, symbol: str, days: int) -> list[Bar]: ...


def is_crypto(symbol: str) -> bool:
    upper = symbol.upper()
    return upper.endswith("-USD") or upper.split("-")[0] in COIN_IDS


def coin_id(symbol: str) -> str:
    return COIN_IDS.get(symbol.upper().split("-")[0], symbol.lower().split("-")[0])


def _cached(key: str) -> list[Bar] | None:
    hit = _CACHE.get(key)
    if hit and time.monotonic() - hit[0] < _CACHE_TTL:
        return hit[1]
    return None


def _store(key: str, bars: list[Bar]) -> list[Bar]:
    _CACHE[key] = (time.monotonic(), bars)
    return bars


def parse_yahoo_chart(payload: dict) -> list[Bar]:
    """Turn a v8 chart response into daily bars, skipping days with no close."""
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        return []

    series = result[0]
    stamps = series.get("timestamp") or []
    quotes = (series.get("indicators") or {}).get("quote") or [{}]
    quote = quotes[0]

    def at(values: list | None, index: int, fallback: float) -> float:
        if not values or index >= len(values) or values[index] is None:
            return fallback
        return float(values[index])

    bars: list[Bar] = []
    closes = quote.get("close") or []
    for index, stamp in enumerate(stamps):
        close = at(closes, index, 0.0)
        if close <= 0:
            continue
        day = datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat()
        bars.append(
            Bar(
                date=day,
                open=at(quote.get("open"), index, close),
                high=at(quote.get("high"), index, close),
                low=at(quote.get("low"), index, close),
                close=close,
                volume=at(quote.get("volume"), index, 0.0),
            )
        )
    return bars


def parse_coingecko(payload: dict) -> list[Bar]:
    bars: list[Bar] = []
    for stamp, price in payload.get("prices", []):
        day = date.fromtimestamp(stamp / 1000).isoformat()
        bars.append(Bar(date=day, open=price, high=price, low=price, close=price, volume=0.0))
    return bars


class YahooSource:
    def __init__(self, timeout: float = 20.0) -> None:
        self._timeout = timeout

    async def history(self, symbol: str, days: int) -> list[Bar]:
        key = f"yahoo:{symbol}:{days}"
        if (hit := _cached(key)) is not None:
            return hit

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=max(days, 5))
        params = {
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1d",
        }
        async with httpx.AsyncClient(timeout=self._timeout, headers=UA, follow_redirects=True) as client:
            response = await client.get(YAHOO_CHART.format(symbol=symbol), params=params)
            response.raise_for_status()
            payload = response.json()
        return _store(key, parse_yahoo_chart(payload)[-days:])


class CoinGeckoFallback:
    def __init__(self, timeout: float = 20.0) -> None:
        self._timeout = timeout

    async def history(self, symbol: str, days: int) -> list[Bar]:
        url = COINGECKO_CHART.format(coin_id=coin_id(symbol))
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}
        async with httpx.AsyncClient(timeout=self._timeout, headers=UA, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        return parse_coingecko(payload)[-days:]


class ResilientPriceSource:
    """Yahoo first; CoinGecko for crypto when Yahoo is unavailable."""

    def __init__(self, timeout: float = 20.0) -> None:
        self._yahoo = YahooSource(timeout)
        self._gecko = CoinGeckoFallback(timeout)

    async def history(self, symbol: str, days: int) -> list[Bar]:
        try:
            bars = await self._yahoo.history(symbol, days)
            if bars:
                return bars
        except Exception:
            if not is_crypto(symbol):
                raise
        return await self._gecko.history(symbol, days)


class FixturePriceSource:
    async def history(self, symbol: str, days: int) -> list[Bar]:
        return sample_bars(days=days)


def build_price_source(settings) -> PriceSource:
    if settings.offline:
        return FixturePriceSource()
    return ResilientPriceSource(settings.http_timeout)
