from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from .models import ParsedPage, Section

WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def _clean_soup(soup: BeautifulSoup) -> None:
    for tag_name in ("script", "style", "nav", "footer", "aside", "noscript"):
        for tag in soup.find_all(tag_name):
            tag.decompose()


def _pick_root(soup: BeautifulSoup) -> Tag | BeautifulSoup:
    return soup.find("main") or soup.find("article") or soup.body or soup


def _extract_title(soup: BeautifulSoup, root: Tag | BeautifulSoup) -> str:
    if soup.title and normalize_whitespace(soup.title.get_text(" ", strip=True)):
        return normalize_whitespace(soup.title.get_text(" ", strip=True))

    first_heading = root.find(["h1", "h2", "h3"])
    if first_heading:
        heading_text = normalize_whitespace(first_heading.get_text(" ", strip=True))
        if heading_text:
            return heading_text

    return "Untitled Page"


def parse_sections(html_or_text: str) -> list[Section]:
    soup = BeautifulSoup(html_or_text, "html.parser")
    root = _pick_root(soup)
    heading_tags = root.find_all(["h1", "h2", "h3"])

    if not heading_tags:
        text = normalize_whitespace(
            soup.get_text(" ", strip=True) if soup.get_text(strip=True) else html_or_text
        )
        return [Section(heading="Untitled", level=1, text=text)]

    sections: list[Section] = []
    for index, heading in enumerate(heading_tags):
        heading_text = normalize_whitespace(heading.get_text(" ", strip=True))
        if not heading_text:
            continue

        next_heading = heading_tags[index + 1] if index + 1 < len(heading_tags) else None
        sections.append(
            Section(
                heading=heading_text,
                level=int(heading.name[1]),
                text=_section_text_between(heading, next_heading),
            )
        )

    return sections or [
        Section(
            heading="Untitled",
            level=1,
            text=normalize_whitespace(soup.get_text(" ", strip=True)),
        )
    ]


def extract_page(html: str, url: str) -> ParsedPage:
    del url
    soup = BeautifulSoup(html, "html.parser")
    _clean_soup(soup)
    root = _pick_root(soup)
    title = _extract_title(soup, root)

    sections = parse_sections(str(root))
    raw_chunks: list[str] = []
    for node in root.find_all(["h1", "h2", "h3", "p", "li"]):
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if text:
            raw_chunks.append(text)
    raw_text = "\n".join(raw_chunks).strip()

    return ParsedPage(title=title, raw_text=raw_text, sections=sections)


def _section_text_between(start_heading: Tag, next_heading: Tag | None) -> str:
    content_parts: list[str] = []
    for node in start_heading.next_elements:
        if node is next_heading:
            break
        if _should_skip_node(node, start_heading):
            continue
        if isinstance(node, Tag) and node.name in {"h1", "h2", "h3"}:
            break
        text = _extract_content_text(node)
        if text:
            content_parts.append(text)
    return "\n".join(content_parts).strip()


def _should_skip_node(node: object, start_heading: Tag) -> bool:
    if node is start_heading:
        return True
    parent = getattr(node, "parent", None)
    return bool(
        parent is not None
        and isinstance(parent, Tag)
        and parent.name in {"script", "style"}
    )


def _extract_content_text(node: object) -> str:
    if not isinstance(node, Tag):
        return ""
    if node.name not in {"p", "li", "pre", "code", "blockquote"}:
        return ""
    return normalize_whitespace(node.get_text(" ", strip=True))
