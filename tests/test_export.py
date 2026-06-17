from pathlib import Path

from knowdiff.export import diff_to_markdown, write_markdown_report
from knowdiff.models import ChangedSection, DiffRecord, DiffResult, Section


def test_diff_to_markdown_includes_all_change_types() -> None:
    diff_record = DiffRecord(
        id=1,
        page_id=1,
        old_snapshot_id=1,
        new_snapshot_id=2,
        diff=DiffResult(
            added=[Section("Added", 2, "new")],
            removed=[Section("Removed", 2, "old")],
            changed=[
                ChangedSection(
                    heading="Changed",
                    level=2,
                    old_text="before",
                    new_text="after",
                    diff="--- before\n+++ after",
                )
            ],
        ),
        created_at=__import__("datetime").datetime(2026, 6, 17, 12, 0, 0),
    )

    output = diff_to_markdown("Example", "https://example.com", diff_record)

    assert "# Knowledge Diff Report: Example" in output
    assert "## Added sections" in output
    assert "## Removed sections" in output
    assert "## Changed sections" in output
    assert "```diff" in output


def test_write_markdown_report_creates_parent_directory(tmp_path: Path) -> None:
    output_path = tmp_path / "reports" / "report.md"
    write_markdown_report(output_path, "# Report\n")
    assert output_path.read_text(encoding="utf-8") == "# Report\n"
