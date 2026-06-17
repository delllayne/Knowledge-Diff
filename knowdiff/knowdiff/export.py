from __future__ import annotations

from pathlib import Path

from .models import DiffRecord


def diff_to_markdown(title: str, url: str, diff_record: DiffRecord) -> str:
    diff = diff_record.diff
    lines = [
        f"# Knowledge Diff Report: {title}",
        "",
        f"- URL: {url}",
        f"- Generated from diff saved at: {diff_record.created_at.isoformat()}",
        "",
    ]

    if diff.added:
        lines.extend(["## Added sections", ""])
        lines.extend([f"- {section.heading}" for section in diff.added])
        lines.append("")

    if diff.removed:
        lines.extend(["## Removed sections", ""])
        lines.extend([f"- {section.heading}" for section in diff.removed])
        lines.append("")

    if diff.changed:
        lines.extend(["## Changed sections", ""])
        for section in diff.changed:
            lines.append(f"### {section.heading}")
            lines.append("")
            lines.append("```diff")
            lines.append(section.diff)
            lines.append("```")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

