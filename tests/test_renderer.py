from __future__ import annotations

from datetime import UTC, datetime

from knowdiff.models import ChangedSection, DiffResult, PageRecord, Section
from knowdiff.renderer import render_add_success, render_diff_report, render_pages
from rich.console import Console


def test_render_pages_for_empty_list() -> None:
    console = Console(record=True, width=120)
    render_pages(console, [])
    assert "No tracked pages yet." in console.export_text()


def test_render_pages_and_diff_report() -> None:
    console = Console(record=True, width=120)
    pages = [
        PageRecord(
            id=1,
            url="https://example.com",
            title="Example",
            created_at=datetime.now(UTC),
            last_checked_at=datetime.now(UTC),
            snapshot_count=2,
        )
    ]
    render_pages(console, pages)
    render_add_success(console, "Example", "https://example.com", 3)
    render_diff_report(
        console,
        "Example",
        "https://example.com",
        DiffResult(
            added=[Section("Added", 2, "text")],
            removed=[Section("Removed", 2, "text")],
            changed=[
                ChangedSection(
                    heading="Changed",
                    level=2,
                    old_text="old",
                    new_text="new",
                    diff="--- old\n+++ new",
                )
            ],
        ),
    )
    output = console.export_text()
    assert "Tracked pages" in output
    assert "Added page:" in output
    assert "CHANGED" in output
    assert "Changed sections:" in output
