# Core data types for skill-router.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

__all__ = [
    "Mode",
    "Platform",
    "RouteResult",
    "SkillMeta",
    "Tier",
]


class Platform(StrEnum):
    """Known agent platforms."""

    CLAUDE = "claude"
    WORKBUDDY = "workbuddy"
    OPENCODE = "opencode"
    OPENCLAW = "openclaw"
    GEMINI = "gemini"
    CODEX = "codex"
    CURSOR = "cursor"
    AGENTS = "agents"
    UNKNOWN = "unknown"


class Tier(StrEnum):
    """Skill tier: project-level or user-level."""

    PROJECT = "project"
    USER = "user"
    NETWORK = "network"


class Mode(StrEnum):
    """Routing mode."""

    SINGLE = "single"
    PIPELINE = "pipeline"
    PARALLEL = "parallel"
    COMPOSE = "compose"
    CHOOSE = "choose"


@dataclass
class SkillMeta:
    """Metadata parsed from a SKILL.md file."""

    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    tier: Tier = Tier.USER
    platform: Platform = Platform.UNKNOWN
    source_path: str = ""


@dataclass
class RouteResult:
    """Result of a routing query."""

    mode: Mode = Mode.SINGLE
    skill: SkillMeta | None = None
    skills: list[SkillMeta] = field(default_factory=list)
    candidates: list[tuple[SkillMeta, float]] = field(default_factory=list)
    score: float = 0.0
    confidence: str = "low"
    action: str = "fallback"
