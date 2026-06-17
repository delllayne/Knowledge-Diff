from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .models import ChangedSection, DiffRecord, DiffResult, PageRecord, Section, SnapshotRecord

DEFAULT_DB_PATH = Path.home() / ".knowdiff" / "knowdiff.db"


class DatabaseError(Exception):
    """Raised for database-related failures."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_db_path() -> Path:
    raw_path = os.environ.get("KNOWDIFF_DB")
    return Path(raw_path).expanduser() if raw_path else DEFAULT_DB_PATH


def _ensure_parent_dir(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _row_to_sections(sections_json: str) -> list[Section]:
    payload = json.loads(sections_json)
    return [Section(**item) for item in payload]


def _row_to_diff(diff_json: str) -> DiffResult:
    payload = json.loads(diff_json)
    return DiffResult(
        added=[Section(**item) for item in payload["added"]],
        removed=[Section(**item) for item in payload["removed"]],
        changed=[ChangedSection(**item) for item in payload["changed"]],
    )


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_db_path()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        try:
            _ensure_parent_dir(self.db_path)
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
            connection.commit()
        except sqlite3.Error as exc:
            if "connection" in locals():
                connection.rollback()
            raise DatabaseError(f"Database error at {self.db_path}: {exc}") from exc
        finally:
            if "connection" in locals():
                connection.close()

    def init(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_checked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    sections_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(page_id) REFERENCES pages(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS diffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id INTEGER NOT NULL,
                    old_snapshot_id INTEGER NOT NULL,
                    new_snapshot_id INTEGER NOT NULL,
                    diff_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(page_id) REFERENCES pages(id) ON DELETE CASCADE,
                    FOREIGN KEY(old_snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
                    FOREIGN KEY(new_snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
                );
                """
            )

    def list_pages(self) -> list[PageRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT p.id, p.url, p.title, p.created_at, p.last_checked_at,
                       COUNT(s.id) AS snapshot_count
                FROM pages p
                LEFT JOIN snapshots s ON s.page_id = p.id
                GROUP BY p.id
                ORDER BY p.created_at ASC
                """
            ).fetchall()
        return [
            self._page_from_row(row)
            for row in rows
        ]

    def get_page(self, url: str) -> PageRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT p.id, p.url, p.title, p.created_at, p.last_checked_at,
                       COUNT(s.id) AS snapshot_count
                FROM pages p
                LEFT JOIN snapshots s ON s.page_id = p.id
                WHERE p.url = ?
                GROUP BY p.id
                """,
                (url,),
            ).fetchone()
        if row is None:
            return None
        return self._page_from_row(row)

    def add_page_with_snapshot(
        self,
        url: str,
        title: str,
        raw_text: str,
        sections: list[Section],
    ) -> PageRecord:
        if self.get_page(url):
            raise DatabaseError(f"URL is already tracked: {url}")

        created_at = utc_now().isoformat()
        content_hash = self.compute_content_hash(raw_text)

        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO pages (url, title, created_at, last_checked_at) VALUES (?, ?, ?, ?)",
                (url, title, created_at, created_at),
            )
            page_id = self._require_row_id(cursor.lastrowid, "page")
            connection.execute(
                """
                INSERT INTO snapshots (page_id, content_hash, raw_text, sections_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    page_id,
                    content_hash,
                    raw_text,
                    json.dumps([section.to_dict() for section in sections]),
                    created_at,
                ),
            )

        page = self.get_page(url)
        if page is None:
            raise DatabaseError("Failed to read page after insertion.")
        return page

    def latest_snapshot(self, page_id: int) -> SnapshotRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, page_id, content_hash, raw_text, sections_json, created_at
                FROM snapshots
                WHERE page_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (page_id,),
            ).fetchone()
        if row is None:
            return None
        return SnapshotRecord(
            id=row["id"],
            page_id=row["page_id"],
            content_hash=row["content_hash"],
            raw_text=row["raw_text"],
            sections=_row_to_sections(row["sections_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def add_snapshot_and_diff(
        self,
        page_id: int,
        title: str,
        raw_text: str,
        sections: list[Section],
        diff: DiffResult,
    ) -> tuple[SnapshotRecord, DiffRecord]:
        old_snapshot = self.latest_snapshot(page_id)
        if old_snapshot is None:
            raise DatabaseError(f"No existing snapshot found for page_id={page_id}.")

        created_at = utc_now().isoformat()
        content_hash = self.compute_content_hash(raw_text)

        with self.connect() as connection:
            connection.execute(
                "UPDATE pages SET title = ?, last_checked_at = ? WHERE id = ?",
                (title, created_at, page_id),
            )
            cursor = connection.execute(
                """
                INSERT INTO snapshots (page_id, content_hash, raw_text, sections_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    page_id,
                    content_hash,
                    raw_text,
                    json.dumps([section.to_dict() for section in sections]),
                    created_at,
                ),
            )
            snapshot_id = self._require_row_id(cursor.lastrowid, "snapshot")
            diff_cursor = connection.execute(
                """
                INSERT INTO diffs (page_id, old_snapshot_id, new_snapshot_id, diff_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (page_id, old_snapshot.id, snapshot_id, json.dumps(diff.to_dict()), created_at),
            )
            diff_id = self._require_row_id(diff_cursor.lastrowid, "diff")

        new_snapshot = self.latest_snapshot(page_id)
        if new_snapshot is None:
            raise DatabaseError("Failed to load newly created snapshot.")
        return new_snapshot, DiffRecord(
            id=diff_id,
            page_id=page_id,
            old_snapshot_id=old_snapshot.id,
            new_snapshot_id=new_snapshot.id,
            diff=diff,
            created_at=datetime.fromisoformat(created_at),
        )

    def touch_page(self, page_id: int, title: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE pages SET title = ?, last_checked_at = ? WHERE id = ?",
                (title, utc_now().isoformat(), page_id),
            )

    def latest_diff(self, page_id: int) -> DiffRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, page_id, old_snapshot_id, new_snapshot_id, diff_json, created_at
                FROM diffs
                WHERE page_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (page_id,),
            ).fetchone()
        if row is None:
            return None
        return DiffRecord(
            id=row["id"],
            page_id=row["page_id"],
            old_snapshot_id=row["old_snapshot_id"],
            new_snapshot_id=row["new_snapshot_id"],
            diff=_row_to_diff(row["diff_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def remove_page(self, url: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM pages WHERE url = ?", (url,))
            return cursor.rowcount > 0

    @staticmethod
    def compute_content_hash(raw_text: str) -> str:
        return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    @staticmethod
    def _require_row_id(row_id: int | None, entity_name: str) -> int:
        if row_id is None:
            raise DatabaseError(f"Failed to create {entity_name} record.")
        return row_id

    @staticmethod
    def _page_from_row(row: sqlite3.Row) -> PageRecord:
        return PageRecord(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_checked_at=(
                datetime.fromisoformat(row["last_checked_at"])
                if row["last_checked_at"]
                else None
            ),
            snapshot_count=row["snapshot_count"],
        )
