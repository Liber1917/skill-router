"""Tests for the platform registry module."""

from __future__ import annotations

import os

from skill_router.scanner.registry import PlatformPaths, PlatformRegistry
from skill_router.types import Platform


# ---------------------------------------------------------------------------
# PlatformPaths
# ---------------------------------------------------------------------------

def test_platform_paths_defaults() -> None:
    """A full-platform entry should store relative paths."""
    pp = PlatformPaths(Platform.CLAUDE, ".claude/skills", ".claude/skills")
    assert pp.platform == Platform.CLAUDE
    assert pp.user_path == ".claude/skills"
    assert pp.project_path == ".claude/skills"


def test_platform_paths_none_user() -> None:
    """CURSOR has no user-level path."""
    pp = PlatformPaths(Platform.CURSOR, None, ".cursor/skills")
    assert pp.user_path is None
    assert pp.project_path == ".cursor/skills"


def test_expand_resolves_home() -> None:
    pp = PlatformPaths(Platform.CLAUDE, ".claude/skills", ".claude/skills")
    user, project = pp.expand(home="/home/test", cwd="/tmp/project")
    assert user == "/home/test/.claude/skills"
    assert project == "/tmp/project/.claude/skills"


def test_expand_none_paths() -> None:
    pp = PlatformPaths(Platform.CURSOR, None, ".cursor/skills")
    user, project = pp.expand(home="/home/test", cwd="/tmp/project")
    assert user is None
    assert project == "/tmp/project/.cursor/skills"


def test_expand_default_home() -> None:
    pp = PlatformPaths(Platform.CLAUDE, ".claude/skills", ".claude/skills")
    user, project = pp.expand(cwd=os.getcwd())
    assert user is not None
    assert user.startswith(os.path.expanduser("~"))
    assert project == os.path.join(os.path.abspath(os.getcwd()), ".claude/skills")


# ---------------------------------------------------------------------------
# PlatformRegistry
# ---------------------------------------------------------------------------


def test_defaults_contains_all_known_platforms() -> None:
    defaults = PlatformRegistry.defaults()
    platforms = {p.platform for p in defaults}
    expected = {
        Platform.CLAUDE,
        Platform.WORKBUDDY,
        Platform.OPENCODE,
        Platform.OPENCLAW,
        Platform.GEMINI,
        Platform.CODEX,
        Platform.CURSOR,
        Platform.AGENTS,
    }
    assert platforms == expected


def test_defaults_paths_correct() -> None:
    defaults = {p.platform: p for p in PlatformRegistry.defaults()}

    assert defaults[Platform.CLAUDE].user_path == ".claude/skills"
    assert defaults[Platform.CLAUDE].project_path == ".claude/skills"

    assert defaults[Platform.CURSOR].user_path is None
    assert defaults[Platform.CURSOR].project_path == ".cursor/skills"

    assert defaults[Platform.OPENCODE].user_path == ".config/opencode/skills"
    assert defaults[Platform.OPENCODE].project_path == ".opencode/skills"


def test_register_custom_paths_for_unknown() -> None:
    # Clean slate for this test
    PlatformRegistry._custom.clear()

    PlatformRegistry.register(Platform.UNKNOWN, ".unknown/skills", ".unknown/skills")

    all_entries = PlatformRegistry.all()
    platforms = {p.platform for p in all_entries}
    assert Platform.UNKNOWN in platforms
    entry = next(p for p in all_entries if p.platform == Platform.UNKNOWN)
    assert entry.user_path == ".unknown/skills"
    assert entry.project_path == ".unknown/skills"

    PlatformRegistry._custom.clear()


def test_all_merges_default_and_custom() -> None:
    PlatformRegistry._custom.clear()

    PlatformRegistry.register(Platform.UNKNOWN, ".unknown/skills", ".unknown/skills")

    all_entries = PlatformRegistry.all()
    assert len(all_entries) == 9  # 8 defaults + 1 custom (UNKNOWN)
    assert Platform.UNKNOWN in {p.platform for p in all_entries}

    PlatformRegistry._custom.clear()


def test_register_can_override_default() -> None:
    PlatformRegistry._custom.clear()

    # Override CLAUDE paths
    PlatformRegistry.register(Platform.CLAUDE, ".my_claude/skills", ".my_claude/skills")
    entry = {p.platform: p for p in PlatformRegistry.all()}[Platform.CLAUDE]
    assert entry.user_path == ".my_claude/skills"
    assert entry.project_path == ".my_claude/skills"

    PlatformRegistry._custom.clear()
