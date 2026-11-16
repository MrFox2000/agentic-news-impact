"""Turning price series into "what moved and what was being written about it"."""

from __future__ import annotations

from datetime import date, timedelta

from .models import Article, Bar, Impact, Move


def daily_changes(bars: list[Bar]) -> list[Move]:
    """Percentage change from the previous close for every bar."""
    moves: list[Move] = []
    for previous, current in zip(bars, bars[1:]):
        if previous.close <= 0:
            continue
        change = (current.close - previous.close) / previous.close * 100
        moves.append(
            Move(date=current.date, close=round(current.close, 2), change_pct=round(change, 2))
        )
    return moves


def biggest_moves(bars: list[Bar], threshold: float = 2.0, limit: int = 5) -> list[Move]:
    """Moves at or beyond `threshold` percent, largest absolute change first."""
    moves = [move for move in daily_changes(bars) if abs(move.change_pct) >= threshold]
    moves.sort(key=lambda move: abs(move.change_pct), reverse=True)
    return moves[:limit]


def align(articles: list[Article], moves: list[Move], lookback: int = 2) -> list[Impact]:
    """Attach each move to the articles published in the `lookback` days before it.

    This is correlation, not causation, and the report says so.
    """
    impacts: list[Impact] = []
    for move in moves:
        day = date.fromisoformat(move.date)
        window_start = (day - timedelta(days=lookback)).isoformat()
        nearby = [
            article for article in articles if window_start <= article.published <= move.date
        ]
        nearby.sort(key=lambda article: article.published)
        impacts.append(Impact(move=move, articles=nearby[:6]))
    return impacts


def summarise(bars: list[Bar]) -> dict[str, float | int | str]:
    """Headline numbers for a symbol over the whole window."""
    if not bars:
        return {}
    first, last = bars[0], bars[-1]
    closes = [bar.close for bar in bars]
    return {
        "first_date": first.date,
        "last_date": last.date,
        "first_close": round(first.close, 2),
        "last_close": round(last.close, 2),
        "change_pct": round((last.close - first.close) / first.close * 100, 2) if first.close else 0.0,
        "high": round(max(closes), 2),
        "low": round(min(closes), 2),
        "bars": len(bars),
    }
