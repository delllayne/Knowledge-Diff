from __future__ import annotations

import difflib
import re

from .models import ChangedSection, DiffResult, Section

HEADING_RE = re.compile(r"\s+")
MAX_DIFF_LINES = 12
MAX_LINE_LENGTH = 140


def normalize_heading(value: str) -> str:
    return HEADING_RE.sub(" ", value).strip().lower()


def _truncate_diff(lines: list[str]) -> str:
    limited = lines[:MAX_DIFF_LINES]
    formatted: list[str] = []
    for line in limited:
        formatted.append(line[:MAX_LINE_LENGTH])
    if len(lines) > MAX_DIFF_LINES:
        formatted.append("... diff truncated ...")
    return "\n".join(formatted)


def _make_diff(old_text: str, new_text: str, heading: str) -> str:
    diff_lines = list(
        difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile=f"{heading} (old)",
            tofile=f"{heading} (new)",
            lineterm="",
            n=1,
        )
    )
    return _truncate_diff(diff_lines)


def compare_sections(old: list[Section], new: list[Section]) -> DiffResult:
    old_map = {normalize_heading(section.heading): section for section in old}
    new_map = {normalize_heading(section.heading): section for section in new}

    added: list[Section] = []
    removed: list[Section] = []
    changed: list[ChangedSection] = []

    for key, new_section in new_map.items():
        old_section = old_map.get(key)
        if old_section is None:
            added.append(new_section)
            continue
        if old_section.text != new_section.text:
            changed.append(
                ChangedSection(
                    heading=new_section.heading,
                    level=new_section.level,
                    old_text=old_section.text,
                    new_text=new_section.text,
                    diff=_make_diff(old_section.text, new_section.text, new_section.heading),
                )
            )

    for key, old_section in old_map.items():
        if key not in new_map:
            removed.append(old_section)

    return DiffResult(added=added, removed=removed, changed=changed)

