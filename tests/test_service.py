from __future__ import annotations

from pathlib import Path

import pytest
from knowdiff.db import Database
from knowdiff.models import ParsedPage, Section
from knowdiff.service import DuplicatePageError, KnowledgeDiffService


@pytest.fixture()
def service(tmp_path: Path) -> KnowledgeDiffService:
    return KnowledgeDiffService(Database(tmp_path / "knowdiff.db"))


def test_add_page_rejects_duplicates(
    service: KnowledgeDiffService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed_page = ParsedPage("Title", "Text", [Section("Intro", 1, "Text")])
    monkeypatch.setattr(service, "_load_parsed_page", lambda url: parsed_page)
    service.add_page("https://example.com")
    with pytest.raises(DuplicatePageError):
        service.add_page("https://example.com")


def test_check_page_detects_change(
    service: KnowledgeDiffService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service,
        "_load_parsed_page",
        lambda url: ParsedPage("Title", "Old", [Section("Intro", 1, "Old")]),
    )
    service.add_page("https://example.com")
    monkeypatch.setattr(
        service,
        "_load_parsed_page",
        lambda url: ParsedPage("Title", "New", [Section("Intro", 1, "New")]),
    )

    outcome = service.check_page("https://example.com")

    assert outcome.changed is True
    assert outcome.diff is not None
    assert len(outcome.diff.changed) == 1


def test_export_latest_diff_writes_file(
    service: KnowledgeDiffService,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        service,
        "_load_parsed_page",
        lambda url: ParsedPage("Title", "Old", [Section("Intro", 1, "Old")]),
    )
    service.add_page("https://example.com")
    monkeypatch.setattr(
        service,
        "_load_parsed_page",
        lambda url: ParsedPage("Title", "New", [Section("Intro", 1, "New")]),
    )
    service.check_page("https://example.com")

    output_path = tmp_path / "report.md"
    result = service.export_latest_diff("https://example.com", output_path)

    assert result == output_path
    assert "Knowledge Diff Report" in output_path.read_text(encoding="utf-8")
