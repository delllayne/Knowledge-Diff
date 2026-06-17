from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .db import Database
from .differ import compare_sections
from .export import diff_to_markdown, write_markdown_report
from .fetcher import KnowDiffError, fetch_page, validate_url
from .models import DiffResult, PageRecord, ParsedPage
from .parser import extract_page


@dataclass(slots=True)
class CheckOutcome:
    title: str
    url: str
    changed: bool
    diff: DiffResult | None


class DuplicatePageError(KnowDiffError):
    """Raised when a URL is already tracked."""


class PageNotTrackedError(KnowDiffError):
    """Raised when a requested URL is not tracked."""


class KnowledgeDiffService:
    def __init__(self, database: Database) -> None:
        self._database = database
        self._database.init()

    def list_pages(self) -> list[PageRecord]:
        return self._database.list_pages()

    def add_page(self, url: str) -> tuple[PageRecord, ParsedPage]:
        validate_url(url)
        if self._database.get_page(url):
            raise DuplicatePageError(f"That URL is already being tracked: {url}")

        parsed_page = self._load_parsed_page(url)
        page = self._database.add_page_with_snapshot(
            url=url,
            title=parsed_page.title,
            raw_text=parsed_page.raw_text,
            sections=parsed_page.sections,
        )
        return page, parsed_page

    def check_page(self, url: str) -> CheckOutcome:
        validate_url(url)
        page = self._database.get_page(url)
        if page is None:
            raise PageNotTrackedError(f"URL is not tracked: {url}")

        parsed_page = self._load_parsed_page(url)
        latest_snapshot = self._database.latest_snapshot(page.id)
        if latest_snapshot is None:
            raise KnowDiffError(f"No snapshot found for tracked URL: {url}")

        diff = compare_sections(latest_snapshot.sections, parsed_page.sections)
        if diff.has_changes:
            self._database.add_snapshot_and_diff(
                page_id=page.id,
                title=parsed_page.title,
                raw_text=parsed_page.raw_text,
                sections=parsed_page.sections,
                diff=diff,
            )
            return CheckOutcome(title=parsed_page.title, url=url, changed=True, diff=diff)

        self._database.touch_page(page.id, parsed_page.title)
        return CheckOutcome(title=parsed_page.title, url=url, changed=False, diff=None)

    def remove_page(self, url: str) -> None:
        validate_url(url)
        if not self._database.remove_page(url):
            raise PageNotTrackedError(f"URL is not tracked: {url}")

    def export_latest_diff(self, url: str, output: Path) -> Path:
        validate_url(url)
        page = self._database.get_page(url)
        if page is None:
            raise PageNotTrackedError(f"URL is not tracked: {url}")

        diff_record = self._database.latest_diff(page.id)
        if diff_record is None:
            raise KnowDiffError(
                f"No previous diff report exists for {url}. "
                "Run 'knowdiff check' after the page changes."
            )

        report = diff_to_markdown(page.title, url, diff_record)
        write_markdown_report(output, report)
        return output

    def _load_parsed_page(self, url: str) -> ParsedPage:
        html = fetch_page(url)
        parsed_page = extract_page(html, url)
        if not parsed_page.raw_text.strip():
            raise KnowDiffError(f"No readable content could be extracted from {url}.")
        return parsed_page
