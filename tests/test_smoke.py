"""Smoke tests for CLI."""

from typer.testing import CliRunner

from skill_router.cli import app

runner = CliRunner()


def test_help_succeeds() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "skill-router" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_platforms_succeeds() -> None:
    result = runner.invoke(app, ["platforms"])
    assert result.exit_code == 0
    assert "claude" in result.stdout.lower()


def test_route_basic() -> None:
    result = runner.invoke(app, ["route", "test prompt"])
    assert result.exit_code == 0


def test_route_with_cwd() -> None:
    result = runner.invoke(app, ["route", "test", "--cwd", "/tmp"])
    assert result.exit_code == 0


def test_search_succeeds() -> None:
    result = runner.invoke(app, ["search", "react component"])
    assert result.exit_code == 0
