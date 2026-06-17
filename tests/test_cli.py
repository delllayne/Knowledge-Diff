from __future__ import annotations

from pathlib import Path

import pytest
from knowdiff.models import DiffResult, PageRecord, ParsedPage, Section
from knowdiff.service import CheckOutcome, DuplicatePageError
from typer.testing import CliRunner

from knowdiff import cli

runner = CliRunner()


def test_list_command_renders_empty_state(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def list_pages(self) -> list[PageRecord]:
            return []

    monkeypatch.setattr(cli, "get_service", lambda: FakeService())
    result = runner.invoke(cli.app, ["list"])
    assert result.exit_code == 0
    assert "No tracked pages yet." in result.stdout


def test_add_command_returns_exit_zero_for_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def add_page(self, url: str) -> tuple[object, ParsedPage]:
            del url
            raise DuplicatePageError("That URL is already being tracked: https://example.com")

    monkeypatch.setattr(cli, "get_service", lambda: FakeService())
    result = runner.invoke(cli.app, ["add", "https://example.com"])
    assert result.exit_code == 0
    assert "already being tracked" in result.stdout


def test_check_command_renders_changed_result(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def check_page(self, url: str) -> CheckOutcome:
            return CheckOutcome(
                title="Example",
                url=url,
                changed=True,
                diff=DiffResult(added=[Section("Added", 2, "text")], removed=[], changed=[]),
            )

        def list_pages(self) -> list[PageRecord]:
            return []

    monkeypatch.setattr(cli, "get_service", lambda: FakeService())
    result = runner.invoke(cli.app, ["check", "https://example.com"])
    assert result.exit_code == 0
    assert "CHANGED" in result.stdout


def test_export_command_reports_destination(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeService:
        def export_latest_diff(self, url: str, output: Path) -> Path:
            del url
            output.write_text("# ok\n", encoding="utf-8")
            return output

    monkeypatch.setattr(cli, "get_service", lambda: FakeService())
    output_path = tmp_path / "report.md"
    result = runner.invoke(cli.app, ["export", "https://example.com", "--output", str(output_path)])
    assert result.exit_code == 0
    assert "Exported report to" in result.stdout
    assert output_path.exists()
