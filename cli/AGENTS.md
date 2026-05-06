# AGENTS.md

You are an AI agent working in the **skill-router** repository.
This file tells you what matters.

## What this repo is

**skill-router** is a cross-platform natural language router for agent skills.
It scans skill directories across 8+ agent platforms and routes user prompts
to the best matching skill using keyword, TF-IDF, and optional LLM matching.

We are **not** a skill engine, marketplace, or execution platform.
We find the right skill — we don't run it.

## What matters

| File | Why it matters |
|------|---------------|
| `src/skill_router/types.py` | Core data types: SkillMeta, RouteResult, Platform, Tier, Mode |
| `src/skill_router/scanner/` | Cross-platform skill directory scanner |
| `src/skill_router/matcher/` | 3-level intent matcher (keyword → TF-IDF → LLM) |
| `src/skill_router/composer/` | Multi-skill relationship detection + orchestration planning |
| `src/skill_router/network/` | skills.sh search + installer (user-confirmed) |
| `src/skill_router/cli.py` | Typer CLI entry point |
| `tests/` | All tests |
| `pyproject.toml` | Python 3.12, uv workspace, hatchling build, ruff + pyright |

## Commands

```bash
uv run pytest                              # run tests
uv run ruff check .                        # lint
uv run ruff format .                       # format
uv run pyright                             # type check
uv run skill-route "prompt"                # route a prompt
uv run skill-route platforms               # list platforms
```

## How to contribute

1. Make changes, write or update tests
2. `uv run ruff check . && uv run ruff format . && uv run pyright && uv run pytest`
3. All three must pass before committing
4. Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`

## What NOT to do

- Do not add HTTP API / serve mode (explicitly excluded from v0.1)
- Do not add skill execution logic (we route, we don't run)
- Do not depend on agent-skill-infra (we're independent)
