from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(slots=True)
class Section:
    heading: str
    level: int
    text: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(slots=True)
class ParsedPage:
    title: str
    raw_text: str
    sections: list[Section]


@dataclass(slots=True)
class ChangedSection:
    heading: str
    level: int
    old_text: str
    new_text: str
    diff: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(slots=True)
class DiffResult:
    added: list[Section]
    removed: list[Section]
    changed: list[ChangedSection]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def to_dict(self) -> dict[str, list[dict[str, str | int]]]:
        return {
            "added": [section.to_dict() for section in self.added],
            "removed": [section.to_dict() for section in self.removed],
            "changed": [section.to_dict() for section in self.changed],
        }


@dataclass(slots=True)
class PageRecord:
    id: int
    url: str
    title: str
    created_at: datetime
    last_checked_at: datetime | None
    snapshot_count: int


@dataclass(slots=True)
class SnapshotRecord:
    id: int
    page_id: int
    content_hash: str
    raw_text: str
    sections: list[Section]
    created_at: datetime


@dataclass(slots=True)
class DiffRecord:
    id: int
    page_id: int
    old_snapshot_id: int
    new_snapshot_id: int
    diff: DiffResult
    created_at: datetime

