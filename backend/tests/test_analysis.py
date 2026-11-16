from __future__ import annotations

from app.analysis import align, biggest_moves, daily_changes, summarise
from app.models import Article, Bar


def bars(closes: list[float]) -> list[Bar]:
    return [
        Bar(date=f"2026-03-{index + 1:02d}", open=c, high=c, low=c, close=c, volume=0.0)
        for index, c in enumerate(closes)
    ]


def test_daily_changes_uses_previous_close() -> None:
    moves = daily_changes(bars([100, 110, 99]))

    assert len(moves) == 2
    assert moves[0].change_pct == 10.0
    assert moves[1].change_pct == -10.0
    assert moves[0].date == "2026-03-02"


def test_biggest_moves_filters_by_threshold() -> None:
    moves = biggest_moves(bars([100, 104, 103, 95]), threshold=3.0)

    assert [move.change_pct for move in moves] == [-7.77, 4.0]


def test_biggest_moves_sorts_by_absolute_change() -> None:
    moves = biggest_moves(bars([100, 101, 110, 105, 90]), threshold=1.0)

    changes = [move.change_pct for move in moves]
    assert changes[0] == -14.29
    assert changes == sorted(changes, key=abs, reverse=True)


def test_align_attaches_articles_from_lookback_window() -> None:
    articles = [
        Article(id="a", title="in window", source="x", url="u1", published="2026-03-09"),
        Article(id="b", title="too early", source="x", url="u2", published="2026-02-20"),
        Article(id="c", title="after the move", source="x", url="u3", published="2026-03-12"),
    ]
    bars_last_drop = bars([100] * 9 + [90])
    moves = biggest_moves(bars_last_drop, threshold=5.0)

    impacts = align(articles, moves, lookback=2)

    assert len(impacts) == 1
    assert impacts[0].move.date == "2026-03-10"
    assert [article.title for article in impacts[0].articles] == ["in window"]


def test_align_handles_no_articles() -> None:
    moves = biggest_moves(bars([100, 90]), threshold=5.0)

    impacts = align([], moves, lookback=2)

    assert impacts[0].articles == []


def test_summarise_reports_window_extremes() -> None:
    summary = summarise(bars([100, 120, 80]))

    assert summary["first_date"] == "2026-03-01"
    assert summary["last_date"] == "2026-03-03"
    assert summary["high"] == 120
    assert summary["low"] == 80
    assert summary["change_pct"] == -20.0
