"""Platform detection — discover installed agent platforms."""

from __future__ import annotations

import os
from pathlib import Path

from skill_router.scanner.registry import PlatformPaths, PlatformRegistry

__all__ = [
    "detect_platforms",
    "resolve_paths",
    "platforms_summary",
]


def detect_platforms(cwd: str = ".", home: str | None = None) -> list[PlatformPaths]:
    """Detect which platforms are present in the current environment.

    Scans user-level paths (``~/.platform/skills/``) and project-level
    paths (``.platform/skills/`` relative to *cwd*).  Returns only
    platforms whose directories actually exist on disk.
    """
    if home is None:
        home = os.path.expanduser("~")

    found: list[PlatformPaths] = []
    for entry in PlatformRegistry.all():
        user_abs, proj_abs = entry.expand(cwd=cwd, home=home)
        user_ok = user_abs is not None and Path(user_abs).is_dir()
        proj_ok = proj_abs is not None and Path(proj_abs).is_dir()
        if user_ok or proj_ok:
            found.append(entry)
    return found


def resolve_paths(
    platform: PlatformPaths,
    cwd: str = ".",
    home: str | None = None,
) -> tuple[str | None, str | None]:
    """Resolve user and project paths for a single platform.

    Returns ``(resolved_user_path, resolved_project_path)``.
    An element is ``None`` when the platform has no path at that level.
    """
    return platform.expand(cwd=cwd, home=home)


def platforms_summary(cwd: str = ".", home: str | None = None) -> list[dict[str, object]]:
    """Return a human-friendly summary of detected platforms."""
    rows: list[dict[str, object]] = []
    for entry in detect_platforms(cwd=cwd, home=home):
        user_abs, proj_abs = resolve_paths(entry, cwd=cwd, home=home)
        rows.append({
            "platform": entry.platform.value,
            "user_path": user_abs,
            "project_path": proj_abs,
        })
    return rows
