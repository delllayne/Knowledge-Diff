from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.panel import Panel

from .models import DiffResult, PageRecord


def format_dt(value: datetime | None) -> str:
    if value is None:
        return "Never"
    return value.astimezone().strftime("%Y-%m-%d %H:%M")


def render_pages(console: Console, pages: list[PageRecord]) -> None:
    if not pages:
        console.print("No tracked pages yet.")
        return

    console.print("[bold]Tracked pages[/bold]\n")
    for index, page in enumerate(pages, start=1):
        console.print(f"{index}. [bold]{page.title}[/bold]")
        console.print(f"   URL: {page.url}")
        console.print(f"   Last checked: {format_dt(page.last_checked_at)}")
        console.print(f"   Snapshots: {page.snapshot_count}")


def render_add_success(console: Console, title: str, url: str, section_count: int) -> None:
    console.print("Added page:")
    console.print(f"[bold]{title}[/bold]")
    console.print(url)
    console.print(f"Sections: {section_count}")


def render_check_header(console: Console, count: int) -> None:
    console.print(f"Checking {count} page{'s' if count != 1 else ''}...\n")


def render_diff_report(console: Console, title: str, url: str, diff: DiffResult | None) -> None:
    if diff is None or not diff.has_changes:
        console.print(f"[green]UNCHANGED[/green]: [bold]{title}[/bold]")
        console.print(url)
        console.print()
        return

    console.print(f"[yellow]CHANGED[/yellow]: [bold]{title}[/bold]")
    console.print(url)
    console.print()

    if diff.added:
        console.print("[bold]Added sections:[/bold]")
        for section in diff.added:
            console.print(f"- {section.heading}")
        console.print()

    if diff.removed:
        console.print("[bold]Removed sections:[/bold]")
        for section in diff.removed:
            console.print(f"- {section.heading}")
        console.print()

    if diff.changed:
        console.print("[bold]Changed sections:[/bold]")
        for changed_section in diff.changed:
            console.print(f"- {changed_section.heading}")
        console.print()


def render_error(console: Console, message: str) -> None:
    console.print(Panel(message, title="Error", border_style="red"))
