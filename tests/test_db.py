from __future__ import annotations

from pathlib import Path

import pytest
from knowdiff.db import Database, DatabaseError
from knowdiff.models import DiffResult, Section


@pytest.fixture()
def database(tmp_path: Path) -> Database:
    db = Database(tmp_path / "knowdiff.db")
    db.init()
    return db


def test_database_add_list_and_remove_operations(database: Database) -> None:
    page = database.add_page_with_snapshot(
        "https://example.com/docs",
        "Example Docs",
        "Hello",
        [Section("Intro", 1, "Hello")],
    )
    pages = database.list_pages()
    assert len(pages) == 1
    assert pages[0].url == "https://example.com/docs"
    assert pages[0].snapshot_count == 1
    assert database.remove_page(page.url) is True
    assert database.list_pages() == []


def test_duplicate_url_handling(database: Database) -> None:
    database.add_page_with_snapshot(
        "https://example.com/docs",
        "Example Docs",
        "Hello",
        [Section("Intro", 1, "Hello")],
    )
    with pytest.raises(DatabaseError):
        database.add_page_with_snapshot(
            "https://example.com/docs",
            "Example Docs",
            "Hello",
            [Section("Intro", 1, "Hello")],
        )


def test_latest_diff_roundtrip(database: Database) -> None:
    page = database.add_page_with_snapshot(
        "https://example.com/docs",
        "Example Docs",
        "Hello",
        [Section("Intro", 1, "Hello")],
    )
    snapshot, diff_record = database.add_snapshot_and_diff(
        page.id,
        "Example Docs",
        "Hello world",
        [Section("Intro", 1, "Hello world")],
        DiffResult(added=[], removed=[], changed=[]),
    )
    assert snapshot.page_id == page.id
    latest = database.latest_diff(page.id)
    assert latest is not None
    assert latest.id == diff_record.id
