"""Tests for core data types."""

from skill_router.types import Mode, Platform, RouteResult, SkillMeta, Tier


def test_skill_meta_defaults() -> None:
    meta = SkillMeta(name="test", description="A test skill")
    assert meta.name == "test"
    assert meta.triggers == []
    assert meta.tier == Tier.USER
    assert meta.platform == Platform.UNKNOWN


def test_skill_meta_full() -> None:
    meta = SkillMeta(
        name="paper-reading",
        description="Read and summarize papers",
        triggers=["paper", "论文"],
        tier=Tier.PROJECT,
        platform=Platform.CLAUDE,
        source_path="/path/to/SKILL.md",
    )
    assert meta.name == "paper-reading"
    assert "论文" in meta.triggers


def test_route_result_defaults() -> None:
    result = RouteResult()
    assert result.mode == Mode.SINGLE
    assert result.confidence == "low"
    assert result.action == "fallback"


def test_route_result_with_skill() -> None:
    meta = SkillMeta(name="test", description="desc")
    result = RouteResult(
        skill=meta,
        mode=Mode.SINGLE,
        score=0.87,
        confidence="high",
        action="invoke",
    )
    assert result.skill is not None
    assert result.skill.name == "test"


def test_platform_values() -> None:
    assert Platform.CLAUDE.value == "claude"
    assert Platform.WORKBUDDY.value == "workbuddy"
    assert Platform.CODEX.value == "codex"
    assert Platform.CURSOR.value == "cursor"


def test_tier_values() -> None:
    assert Tier.PROJECT.value == "project"
    assert Tier.USER.value == "user"
    assert Tier.NETWORK.value == "network"


def test_mode_values() -> None:
    assert Mode.SINGLE.value == "single"
    assert Mode.PIPELINE.value == "pipeline"
    assert Mode.PARALLEL.value == "parallel"
    assert Mode.COMPOSE.value == "compose"
    assert Mode.CHOOSE.value == "choose"


def test_version_importable() -> None:
    from skill_router import __version__

    assert __version__ == "0.1.0"
