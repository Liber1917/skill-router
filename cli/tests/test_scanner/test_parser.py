"""Tests for SKILL.md frontmatter parser."""

from pathlib import Path

import pytest

from skill_router.scanner.parser import parse_skill_md


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_skill(tmp_path: Path) -> Path:
    """Create a SKILL.md with full frontmatter."""
    path = tmp_path / "SKILL.md"
    path.write_text(
        """\
---
name: paper-reading
description: Read and summarize academic papers
triggers:
  - paper
  - 论文
  - academic
---

## Summary

Summarizes research papers from PDF or URL.

## Usage

1. Provide a paper URL or PDF path
2. The skill extracts key findings
"""
    )
    return path


@pytest.fixture
def inline_triggers_skill(tmp_path: Path) -> Path:
    """Create a SKILL.md with inline triggers."""
    path = tmp_path / "SKILL.md"
    path.write_text(
        """\
---
name: code-review
description: Review code changes
triggers: review
---
"""
    )
    return path


@pytest.fixture
def no_frontmatter_skill(tmp_path: Path) -> Path:
    """Create a SKILL.md with no frontmatter."""
    path = tmp_path / "SKILL.md"
    path.write_text(
        """\
# My Skill

Just some markdown content.
"""
    )
    return path


@pytest.fixture
def empty_frontmatter_skill(tmp_path: Path) -> Path:
    """Create a SKILL.md with empty frontmatter."""
    path = tmp_path / "SKILL.md"
    path.write_text(
        """\
---
---

Some body content.
"""
    )
    return path


@pytest.fixture
def partial_frontmatter_skill(tmp_path: Path) -> Path:
    """Create a SKILL.md with only description, no name."""
    path = tmp_path / "my-custom-skill" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        """\
---
description: A skill with no explicit name
---
"""
    )
    return path


@pytest.fixture
def unusual_filename_skill(tmp_path: Path) -> Path:
    """SKILL.md with an unusual parent directory name."""
    path = tmp_path / "data-analyzer-v2" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: data-analyzer\n---\n")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestParseSkillMd:
    def test_parses_full_frontmatter(self, sample_skill: Path) -> None:
        meta = parse_skill_md(sample_skill)
        assert meta.name == "paper-reading"
        assert meta.description == "Read and summarize academic papers"
        assert meta.triggers == ["paper", "论文", "academic"]
        assert meta.source_path == str(sample_skill.resolve())

    def test_parses_inline_triggers(self, inline_triggers_skill: Path) -> None:
        meta = parse_skill_md(inline_triggers_skill)
        assert meta.name == "code-review"
        assert meta.triggers == ["review"]

    def test_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_skill_md("/nonexistent/path/SKILL.md")

    def test_no_frontmatter_fallback_to_filename(
        self, no_frontmatter_skill: Path
    ) -> None:
        meta = parse_skill_md(no_frontmatter_skill)
        assert meta.name == "SKILL"  # stem of "SKILL.md"
        assert meta.description == ""
        assert meta.triggers == []

    def test_empty_frontmatter(self, empty_frontmatter_skill: Path) -> None:
        meta = parse_skill_md(empty_frontmatter_skill)
        assert meta.name == "SKILL"
        assert meta.description == ""
        assert meta.triggers == []

    def test_partial_frontmatter_uses_fallback_name(
        self, partial_frontmatter_skill: Path,
    ) -> None:
        meta = parse_skill_md(partial_frontmatter_skill)
        # No explicit name in frontmatter — fall back to file stem ("SKILL")
        assert meta.name == "SKILL"
        assert meta.description == "A skill with no explicit name"

    def test_explicit_name_in_frontmatter(
        self, unusual_filename_skill: Path,
    ) -> None:
        meta = parse_skill_md(unusual_filename_skill)
        # Explicit name should be used, not directory stem
        assert meta.name == "data-analyzer"
        assert meta.source_path == str(unusual_filename_skill.resolve())

    def test_source_path_is_set(self, sample_skill: Path) -> None:
        meta = parse_skill_md(sample_skill)
        assert meta.source_path.endswith("/SKILL.md")

    def test_resolves_source_path(self, sample_skill: Path) -> None:
        meta = parse_skill_md(str(sample_skill))
        assert meta.source_path == str(sample_skill.resolve())

    def test_accepts_str_path(self, sample_skill: Path) -> None:
        meta = parse_skill_md(str(sample_skill))
        assert meta.name == "paper-reading"

    def test_accepts_path_object(self, sample_skill: Path) -> None:
        meta = parse_skill_md(sample_skill)
        assert meta.name == "paper-reading"


class TestFrontmatterEdgeCases:
    def test_no_triggers(self, tmp_path: Path) -> None:
        path = tmp_path / "SKILL.md"
        path.write_text("---\nname: simple\n---\n")
        meta = parse_skill_md(path)
        assert meta.triggers == []

    def test_multiple_crlf_lines(self, tmp_path: Path) -> None:
        """CRLF line endings should still parse correctly."""
        path = tmp_path / "SKILL.md"
        path.write_bytes(
            b"---\r\nname: crlf-skill\r\ndescription: CRLF test\r\n---\r\n"
        )
        meta = parse_skill_md(path)
        assert meta.name == "crlf-skill"
        assert meta.description == "CRLF test"

    def test_whitespace_around_key(self, tmp_path: Path) -> None:
        path = tmp_path / "SKILL.md"
        path.write_text(
            "---\n  name  :  spaced-name  \ndescription:  has trailing  \n---\n"
        )
        meta = parse_skill_md(path)
        assert meta.name == "spaced-name"
        assert meta.description == "has trailing"

    def test_case_insensitive_keys(self, tmp_path: Path) -> None:
        path = tmp_path / "SKILL.md"
        path.write_text("---\nNAME: caps-test\n---\n")
        meta = parse_skill_md(path)
        assert meta.name == "caps-test"

    def test_triggers_inline_and_list_unused(self, tmp_path: Path) -> None:
        """Only inline trigger form."""
        path = tmp_path / "SKILL.md"
        path.write_text("---\ntriggers: single_word_only\n---\n")
        meta = parse_skill_md(path)
        assert meta.triggers == ["single_word_only"]
