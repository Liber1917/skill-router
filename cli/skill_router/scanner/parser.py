"""SKILL.md frontmatter parser for skill-router.

Extracts metadata (name, description, triggers) from the YAML frontmatter
of SKILL.md files. Returns a ``SkillMeta`` dataclass.
"""

from __future__ import annotations

import re
from pathlib import Path

from skill_router.types import SkillMeta

# Matches YAML frontmatter delimited by --- ... ---
_FRONTMATTER_RE = re.compile(
    r"^\s*---\s*\n(.*?)\n---\s*\n?",
    re.DOTALL,
)

__all__ = [
    "parse_skill_md",
]


def parse_skill_md(path: str | Path) -> SkillMeta:
    """Parse metadata from a SKILL.md file.

    Reads the file, extracts YAML-like frontmatter delimited by ``---``,
    and returns a ``SkillMeta`` populated with ``name``, ``description``,
    and ``triggers``.

    Args:
        path: Path to the SKILL.md file.

    Returns:
        SkillMeta with fields parsed from frontmatter.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Skill file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    match = _FRONTMATTER_RE.match(content)
    if not match:
        return SkillMeta(
            name=file_path.stem,
            description="",
            source_path=str(file_path.resolve()),
        )

    raw = match.group(1)
    meta = _parse_frontmatter_lines(raw, file_path.stem)
    meta.source_path = str(file_path.resolve())
    return meta


def _parse_frontmatter_lines(raw: str, fallback_name: str) -> SkillMeta:
    """Parse simple YAML-like frontmatter into a SkillMeta.

    Only handles flat key-value pairs and ``- `` prefixed list items.
    """
    name: str = fallback_name
    description: str = ""
    triggers: list[str] = []
    in_triggers_list: bool = False

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            in_triggers_list = False
            continue

        # List item
        if stripped.startswith("- "):
            if in_triggers_list:
                triggers.append(stripped[2:].strip())
            continue

        # Key-value pair
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip().lower()
            value = value.strip()

            in_triggers_list = False

            if key == "name" and value:
                name = value
            elif key == "description" and value:
                description = value
            elif key == "triggers":
                if value:
                    # Inline form: triggers: single_word
                    triggers.append(value)
                else:
                    # List form follows on subsequent lines
                    in_triggers_list = True

    return SkillMeta(
        name=name,
        description=description,
        triggers=triggers,
    )
