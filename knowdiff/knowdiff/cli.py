from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .db import Database, DatabaseError
from .fetcher import FetchError, KnowDiffError, ValidationError
from .renderer import (
    render_add_success,
    render_check_header,
    render_diff_report,
    render_error,
    render_pages,
)
from .service import CheckOutcome, DuplicatePageError, KnowledgeDiffService

app = typer.Typer(help="Track documentation snapshots and inspect what changed.")
console = Console()
OUTPUT_OPTION = typer.Option(..., "--output", "-o")


def get_service() -> KnowledgeDiffService:
    database = Database()
    return KnowledgeDiffService(database)


def _handle_error(exc: Exception) -> None:
    render_error(console, str(exc))
    raise typer.Exit(code=1)


@app.command()
def add(url: str) -> None:
    """Track a new page and save the first snapshot."""
    try:
        service = get_service()
        page, parsed_page = service.add_page(url)
        render_add_success(console, page.title, page.url, len(parsed_page.sections))
    except DuplicatePageError as exc:
        console.print(str(exc))
        raise typer.Exit(code=0) from None
    except (ValidationError, FetchError, DatabaseError, KnowDiffError) as exc:
        _handle_error(exc)


@app.command(name="list")
def list_pages() -> None:
    """List tracked pages."""
    try:
        service = get_service()
        render_pages(console, service.list_pages())
    except DatabaseError as exc:
        _handle_error(exc)


def _render_outcome(outcome: CheckOutcome) -> None:
    render_diff_report(console, outcome.title, outcome.url, outcome.diff)


@app.command()
def check(url: str | None = typer.Argument(None)) -> None:
    """Check all tracked pages or a single tracked URL."""
    try:
        service = get_service()
        if url:
            render_check_header(console, 1)
            _render_outcome(service.check_page(url))
            return

        pages = service.list_pages()
        if not pages:
            console.print("No tracked pages yet.")
            return

        render_check_header(console, len(pages))
        had_errors = False
        for page in pages:
            try:
                _render_outcome(service.check_page(page.url))
            except (FetchError, DatabaseError, KnowDiffError) as exc:
                had_errors = True
                render_error(console, str(exc))

        if had_errors:
            raise typer.Exit(code=1)
    except (ValidationError, FetchError, DatabaseError, KnowDiffError) as exc:
        _handle_error(exc)


@app.command()
def remove(url: str) -> None:
    """Remove a tracked page and its snapshots."""
    try:
        service = get_service()
        service.remove_page(url)
        console.print(f"Removed tracked page: {url}")
    except (ValidationError, DatabaseError, KnowDiffError) as exc:
        _handle_error(exc)


@app.command()
def export(url: str, output: Path = OUTPUT_OPTION) -> None:
    """Export the latest diff report for a tracked URL to Markdown."""
    try:
        service = get_service()
        service.export_latest_diff(url, output)
        console.print(f"Exported report to {output}")
    except (ValidationError, DatabaseError, KnowDiffError) as exc:
        _handle_error(exc)


if __name__ == "__main__":
    app()
