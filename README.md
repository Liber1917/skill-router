# skill-router

A pure SKILL.md router for agent skills. Install it like any other skill.
Your AI reads the routing rules and automatically loads the right skill for
whatever the user asks.

```bash
# Install: copy SKILL.md to your skills directory
cp SKILL.md ~/.claude/skills/skill-router/SKILL.md

# Or use npx skills
npx skills add Liber1917/skill-router
```

## How it works

This is a meta-skill. It doesn't do work itself — it routes user intent to the
best matching installed skill.

```
User: "帮我写一篇论文综述"
  → skill-router reads routing table
  → Matches "论文" to arxiv-reader + "综述" to content-ops
  → pipeline: arxiv-reader → content-ops
  → Loads both, executes in sequence
```

## What it covers

- **50+ routing rules** — writing, code, research, design, data, workflow, more
- **Multi-skill patterns** — pipeline, parallel, compose
- **8+ platforms** — Claude Code, WorkBuddy, OpenCode, Gemini CLI, Codex etc.
- **Network fallback** — `npx skills find` when nothing local matches
- **Self-maintaining** — add new rules as you discover them

## Quick start

1. Copy `SKILL.md` to your skills directory
2. Start asking your AI to do things without naming a skill
3. The AI reads this file and routes automatically

## CLI (optional)

A Python CLI tool lives in `cli/` for power users who want TF-IDF matching
or batch routing table maintenance. Purely optional — the SKILL.md works alone.

```bash
pip install cli/   # or: cd cli && pip install -e .
skill-route "帮我写论文"
```

## Design

Why a SKILL.md and not a Python package? Because GSD proved that routing is
fundamentally an AI-interpretable task, not a computational one. The AI reads
the routing rules, understands intent, and makes better routing decisions than
any TF-IDF vector could. The SKILL.md is self-contained, zero-install, and
works across every agent platform.

## License

MIT
