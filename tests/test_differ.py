from knowdiff.differ import compare_sections
from knowdiff.models import Section


def test_detects_added_sections() -> None:
    old = [Section("Intro", 1, "Hello")]
    new = [Section("Intro", 1, "Hello"), Section("New", 2, "World")]
    diff = compare_sections(old, new)
    assert [section.heading for section in diff.added] == ["New"]
    assert not diff.removed
    assert not diff.changed


def test_detects_removed_sections() -> None:
    old = [Section("Intro", 1, "Hello"), Section("Gone", 2, "Bye")]
    new = [Section("Intro", 1, "Hello")]
    diff = compare_sections(old, new)
    assert [section.heading for section in diff.removed] == ["Gone"]
    assert not diff.added
    assert not diff.changed


def test_detects_changed_sections() -> None:
    old = [Section("Intro", 1, "Old text")]
    new = [Section("Intro", 1, "New text")]
    diff = compare_sections(old, new)
    assert len(diff.changed) == 1
    assert diff.changed[0].heading == "Intro"
    assert "--- Intro (old)" in diff.changed[0].diff
    assert "+++ Intro (new)" in diff.changed[0].diff


def test_matches_headings_after_normalization() -> None:
    old = [Section("Reactive Dependencies", 2, "Old")]
    new = [Section("reactive   dependencies", 2, "New")]
    diff = compare_sections(old, new)
    assert not diff.added
    assert not diff.removed
    assert len(diff.changed) == 1
