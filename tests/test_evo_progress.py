from __future__ import annotations

from scribesim.evo.compose import render_folio_lines


def test_render_folio_lines_emits_line_progress():
    events: list[dict] = []

    render_folio_lines(
        ["abc", "def"],
        dpi=72.0,
        evolve=False,
        verbose=False,
        progress_callback=events.append,
        progress_granularity="line",
    )

    stages = [e["stage"] for e in events]
    assert stages == ["line_start", "line_complete", "line_start", "line_complete"]


def test_render_folio_lines_emits_word_progress_when_requested():
    events: list[dict] = []

    render_folio_lines(
        ["abc def"],
        dpi=72.0,
        evolve=False,
        verbose=False,
        progress_callback=events.append,
        progress_granularity="word",
    )

    stages = [e["stage"] for e in events]
    assert stages[0] == "line_start"
    assert stages[-1] == "line_complete"
    assert any(e["stage"] == "word_complete" for e in events)
