"""Skill Router CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from skill_router import __version__

app = typer.Typer(
    name="skill-route",
    help="Cross-platform natural language router for agent skills",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"skill-router v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """skill-router: find the right agent skill wherever it lives."""
    pass


@app.command()
def route(
    prompt: str = typer.Argument(..., help="Natural language prompt to route"),
    cwd: Path = typer.Option(
        Path.cwd(),
        "--cwd",
        help="Project working directory",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output JSON instead of rich table",
    ),
) -> None:
    """Route a prompt to the best matching skill."""
    console.print(f"[bold]Routing:[/] {prompt}")
    console.print(f"[dim]cwd:[/] {cwd}")
    if json_output:
        console.print('{"status": "not_implemented"}')
    else:
        console.print("[yellow]Phase 0 scaffold — routing not yet implemented[/]")


@app.command()
def platforms() -> None:
    """List detected agent platforms."""
    table = Table(title="Detected Platforms")
    table.add_column("Platform", style="cyan")
    table.add_column("User-level", style="green")
    table.add_column("Project-level", style="green")
    table.add_column("Status")
    table.add_row("claude", "~/.claude/skills/", ".claude/skills/", "—")
    table.add_row("workbuddy", "~/.workbuddy/skills/", ".workbuddy/skills/", "—")
    table.add_row("opencode", "~/.config/opencode/skills/", ".opencode/skills/", "—")
    table.add_row("openclaw", "~/.openclaw/skills/", ".openclaw/skills/", "—")
    table.add_row("gemini", "~/.gemini/skills/", ".gemini/skills/", "—")
    table.add_row("codex", "~/.codex/skills/", ".codex/skills/", "—")
    table.add_row("cursor", "—", ".cursor/skills/", "—")
    table.add_row("universal", "~/.agents/skills/", ".agents/skills/", "—")
    console.print(table)
    console.print("\n[yellow]Platform detection not yet implemented[/]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
) -> None:
    """Search skills.sh for a skill."""
    console.print(f"[bold]Searching:[/] {query}")
    console.print("[yellow]Network search not yet implemented[/]")


@app.command()
def rebuild() -> None:
    """Rebuild the skill index."""
    console.print("[yellow]Index rebuild not yet implemented[/]")


@app.command(name="list")
def list_skills() -> None:
    """List all indexed skills."""
    console.print("[yellow]Index list not yet implemented[/]")


@app.command()
def stats() -> None:
    """Show skill index statistics."""
    console.print("[yellow]Index stats not yet implemented[/]")


if __name__ == "__main__":
    app()
