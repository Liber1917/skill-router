# skill-router

A cross-platform natural language router for agent skills.

Find the right skill wherever it lives — across Claude Code, WorkBuddy, OpenCode,
Gemini CLI, Codex, Cursor, and more.

```bash
# Route a prompt to the best matching skill
skill-route "帮我写一篇论文综述"

# → paper-reading (0.87 · user · claude)
#   @ ~/.claude/skills/paper-reading/SKILL.md
```

## Key features

- **Cross-platform** — scans 8+ agent platform skill directories automatically
- **Intent-aware routing** — keyword → TF-IDF → LLM (3 levels)
- **Multi-skill detection** — detects pipeline, parallel, and compose relationships
- **Network fallback** — searches skills.sh when nothing matches locally
- **Zero config** — works out of box, auto-detects which platforms you use

## Platforms supported

| Platform | User-level | Project-level |
|----------|-----------|---------------|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| WorkBuddy | `~/.workbuddy/skills/` | `.workbuddy/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `.opencode/skills/` |
| OpenClaw | `~/.openclaw/skills/` | `.openclaw/skills/` |
| Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/` |
| Codex CLI | `~/.codex/skills/` | `.codex/skills/` |
| Cursor | — | `.cursor/skills/` |
| Universal | `~/.agents/skills/` | `.agents/skills/` |

## Install

```bash
pip install skill-router
```

## Usage

```bash
# Route a prompt
skill-route "write a react component"

# Route with context
skill-route "fix this bug" --cwd /path/to/project

# List detected platforms
skill-route platforms

# Index stats
skill-route index stats

# JSON output (for scripts)
skill-route "review my code" --json

# Search skills.sh
skill-route search "react component generator"
```

## License

MIT
