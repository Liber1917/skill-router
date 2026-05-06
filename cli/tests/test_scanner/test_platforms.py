"""Tests for the platform detection module."""

from __future__ import annotations

import os
from pathlib import Path

from skill_router.scanner.platforms import detect_platforms, platforms_summary, resolve_paths
from skill_router.scanner.registry import PlatformPaths, PlatformRegistry
from skill_router.types import Platform


# ---------------------------------------------------------------------------
# detect_platforms
# ---------------------------------------------------------------------------


def test_detect_no_platforms(tmp_path: Path) -> None:
    """When no platform directories exist, returns empty list."""
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    assert found == []


def test_detect_user_level_only(tmp_path: Path) -> None:
    """A platform with only its user-level directory present."""
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    # Create CLAUDE user-level dir
    (home / ".claude" / "skills").mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    platforms = {p.platform for p in found}
    assert Platform.CLAUDE in platforms


def test_detect_project_level_only(tmp_path: Path) -> None:
    """A platform with only its project-level directory present."""
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    # Create WORKBUDDY project-level dir
    (cwd / ".workbuddy" / "skills").mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    platforms = {p.platform for p in found}
    assert Platform.WORKBUDDY in platforms


def test_detect_both_levels(tmp_path: Path) -> None:
    """Platform appears once even when both dirs exist."""
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    (home / ".claude" / "skills").mkdir(parents=True)
    (cwd / ".claude" / "skills").mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    claude_entries = [e for e in found if e.platform == Platform.CLAUDE]
    assert len(claude_entries) == 1  # deduplicated


def test_detect_multiple_platforms(tmp_path: Path) -> None:
    """Multiple platforms are detected simultaneously."""
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    (home / ".claude" / "skills").mkdir(parents=True)
    (home / ".codex" / "skills").mkdir(parents=True)
    (cwd / ".gemini" / "skills").mkdir(parents=True)
    (cwd / ".cursor" / "skills").mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    platforms = {p.platform for p in found}
    assert platforms == {Platform.CLAUDE, Platform.CODEX, Platform.GEMINI, Platform.CURSOR}


def test_detect_cursor_only_project(tmp_path: Path) -> None:
    """CURSOR should only be detected via its project-level path."""
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    # CURSOR should NOT be detected from user-level
    (home / ".cursor" / "skills").mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    platforms = {p.platform for p in found}
    assert Platform.CURSOR not in platforms

    # CURSOR SHOULD be detected from project-level
    (cwd / ".cursor" / "skills").mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    platforms = {p.platform for p in found}
    assert Platform.CURSOR in platforms


def test_detect_with_custom_platform(tmp_path: Path) -> None:
    """Custom registered platforms are also detected."""
    PlatformRegistry._custom.clear()

    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    PlatformRegistry.register(Platform.UNKNOWN, ".unknown/skills", ".unknown/skills")
    (home / ".unknown" / "skills").mkdir(parents=True)

    found = detect_platforms(cwd=str(cwd), home=str(home))
    platforms = {p.platform for p in found}
    assert Platform.UNKNOWN in platforms

    PlatformRegistry._custom.clear()


# ---------------------------------------------------------------------------
# resolve_paths
# ---------------------------------------------------------------------------


def test_resolve_paths_full(tmp_path: Path) -> None:
    pp = PlatformPaths(Platform.CLAUDE, ".claude/skills", ".claude/skills")
    user, project = resolve_paths(pp, cwd="/tmp/project", home="/home/test")
    assert user == "/home/test/.claude/skills"
    assert project == "/tmp/project/.claude/skills"


def test_resolve_paths_no_user(tmp_path: Path) -> None:
    pp = PlatformPaths(Platform.CURSOR, None, ".cursor/skills")
    user, project = resolve_paths(pp, cwd="/tmp/project", home="/home/test")
    assert user is None
    assert project == "/tmp/project/.cursor/skills"


# ---------------------------------------------------------------------------
# platforms_summary
# ---------------------------------------------------------------------------


def test_platforms_summary(tmp_path: Path) -> None:
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    cwd.mkdir(parents=True)

    (home / ".claude" / "skills").mkdir(parents=True)
    (cwd / ".cursor" / "skills").mkdir(parents=True)

    summary = platforms_summary(cwd=str(cwd), home=str(home))
    assert len(summary) == 2

    platforms = {r["platform"] for r in summary}
    assert platforms == {"claude", "cursor"}
