# AGENTS.md — skill-router

## What this repo is

**skill-router** is a pure SKILL.md routing skill. It routes user prompts to the
best matching installed skill. No Python, no install, no build.

The primary artifact is `SKILL.md` at the repo root. Copy it to any agent
platform's skills directory and it works.

## Repo structure

```
SKILL.md          ← the product (copy this to ~/.claude/skills/skill-router/)
README.md         ← usage instructions
cli/              ← optional Python CLI (parser, registry, TF-IDF matching)
  pyproject.toml  ← pip installable (pip install cli/)
  types.py        ← shared data types
  scanner/        ← cross-platform skill directory scanner
  matcher/        ← (future) TF-IDF matcher
  composer/       ← (future) multi-skill orchestration
  network/        ← (future) skills.sh search
  tests/          ← 36 tests ✅
```

## Important

- The SKILL.md IS the product. Everything else is optional.
- The Python CLI is an optional companion, not the main tool.
- The routing table in SKILL.md is self-maintaining — add new rules as you discover them.
