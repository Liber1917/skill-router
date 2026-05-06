"""Platform registry — known platform path definitions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import ClassVar

from skill_router.types import Platform

__all__ = [
    "PlatformPaths",
    "PlatformRegistry",
]


@dataclass
class PlatformPaths:
    """Path configuration for a single platform.

    Both paths are stored relative.  Caller resolves them against
    the appropriate base directory (``$HOME`` for user-level,
    working directory for project-level) at scan time.
    """

    platform: Platform
    user_path: str | None   # relative, e.g. ".claude/skills"; None → no user-level dir
    project_path: str | None  # relative to cwd; None → no project-level dir

    def expand(self, cwd: str = ".", home: str | None = None) -> tuple[str | None, str | None]:
        """Expand to absolute paths.

        Returns ``(resolved_user_path, resolved_project_path)``.
        Either element may be ``None`` if the platform has no path
        at that level.
        """
        if home is None:
            home = os.path.expanduser("~")

        user = os.path.join(home, self.user_path) if self.user_path else None
        project = os.path.join(os.path.abspath(cwd), self.project_path) if self.project_path else None
        return user, project


class PlatformRegistry:
    """Registry of known agent platforms with their default paths."""

    _custom: ClassVar[dict[Platform, tuple[str | None, str | None]]] = {}

    @staticmethod
    def defaults() -> list[PlatformPaths]:
        """Return the built-in set of known platform path definitions."""
        return [
            PlatformPaths(Platform.CLAUDE, ".claude/skills", ".claude/skills"),
            PlatformPaths(Platform.WORKBUDDY, ".workbuddy/skills", ".workbuddy/skills"),
            PlatformPaths(Platform.OPENCODE, ".config/opencode/skills", ".opencode/skills"),
            PlatformPaths(Platform.OPENCLAW, ".openclaw/skills", ".openclaw/skills"),
            PlatformPaths(Platform.GEMINI, ".gemini/skills", ".gemini/skills"),
            PlatformPaths(Platform.CODEX, ".codex/skills", ".codex/skills"),
            PlatformPaths(Platform.CURSOR, None, ".cursor/skills"),
            PlatformPaths(Platform.AGENTS, ".agents/skills", ".agents/skills"),
        ]

    @staticmethod
    def register(platform: Platform, user_path: str | None, project_path: str | None) -> None:
        """Register a custom platform."""

        PlatformRegistry._custom[platform] = (user_path, project_path)

    @staticmethod
    def all() -> list[PlatformPaths]:
        """Return default platforms merged with any custom registrations."""
        by_platform = {p.platform: p for p in PlatformRegistry.defaults()}
        for platform, (user_path, project_path) in PlatformRegistry._custom.items():
            by_platform[platform] = PlatformPaths(platform, user_path, project_path)
        return list(by_platform.values())
