---
name: skill-router
description: Scan, discover, and route user intent to the best matching installed skill. Dynamic routing from your actual skills — no hardcoded rules.
---

# Skill Router

Route any user request to the right skill. The router doesn't guess what
skills you *might* have — it scans what you *actually* have and matches
against those.

Works across Claude Code, WorkBuddy, OpenCode, Gemini CLI, Codex, OpenClaw,
Cursor, and any platform that uses `SKILL.md`.

## When to use

- User says something ambiguous — you're not sure which skill to use.
- User doesn't know what skills are available.
- User wants to do something that might span multiple skills.
- User mentions a task and you want to check if a relevant skill exists.

**Do NOT use** when the user explicitly names a skill (`/skill-name` or `@skill`).

## How the router works

The router has three phases. Always execute them in order.

### Phase 1: Scan — discover all available skills

Read every skill directory you can find. For each skill, read its `SKILL.md`
and extract three things: **name**, **description**, and **triggers** (from
the YAML frontmatter).

Check these locations in order of priority:

| Priority | Level | Paths to scan |
|----------|-------|---------------|
| 1st | **Project** | `.claude/skills/*/SKILL.md`, `.workbuddy/skills/*/SKILL.md`, `.opencode/skills/*/SKILL.md`, `.gemini/skills/*/SKILL.md`, `.codex/skills/*/SKILL.md`, `.openclaw/skills/*/SKILL.md`, `.cursor/skills/*/SKILL.md`, `.agents/skills/*/SKILL.md` |
| 2nd | **User** | `~/.claude/skills/*/SKILL.md`, `~/.workbuddy/skills/*/SKILL.md`, `~/.config/opencode/skills/*/SKILL.md`, `~/.gemini/skills/*/SKILL.md`, `~/.codex/skills/*/SKILL.md`, `~/.openclaw/skills/*/SKILL.md`, `~/.agents/skills/*/SKILL.md` |

**Deduplication rule**: If the same skill name exists at both project and user
level, prefer the project-level one (it's more context-specific).

Build a table like this in your working memory:

```
Available skills:
├── paper-reading    — Read and summarize academic papers. Triggers: paper, 论文, research
├── git-commit-writer — Write conventional commit messages. Triggers: commit, 提交, git
├── code-reviewer    — Review code for bugs and style issues. Triggers: review, 审查, lint
└── ...
```

### Phase 2: Match — find the best skill for the user's intent

Compare the user's request against every skill's **name**, **description**,
and **triggers** field.

**Matching rules** (use your judgment — you understand semantics, not just
keywords):

1. **Exact trigger match** → High confidence. User says "论文", skill has
   `triggers: [论文]`. Immediately load that skill.

2. **Semantic match** → Medium confidence. User says "帮我理一下参考文献的
   逻辑", no exact trigger, but `paper-reading`'s description matches.
   Present this option to the user.

3. **Broad match** → Low confidence. User says "写点东西" and multiple
   writing-related skills exist. Show them as options.

4. **No match** → Fallback to network search (Phase 3).

### Phase 3: Fallback — search community skills

If no installed skill matches:

1. Run: `npx skills find "<describe the user's need in 5-10 English words>"`
2. Read the results. Select the most relevant ones.
3. Present up to 3 options to the user:
   - Show the skill name, description, and install command.
   - Ask: "Would you like to install one of these?"
4. If they say yes: `npx skills add <owner/repo@skill> -g -y`
5. After install, the skill is immediately available.

> **Note**: If `npx` is not available, fall back to suggesting the user
> search manually at https://skills.sh or https://github.com/topics/agent-skills.

---

## Multi-skill routing

Some requests need multiple skills. Detect and handle these patterns:

| Pattern | What it means | When to use |
|---------|---------------|-------------|
| **Pipeline** | Skill A's output feeds into Skill B | "Read this paper and write a summary" — need to read first, then write |
| **Parallel** | Skills A and B are independent | "Check GitHub trends and search for AI news" — both independent |
| **Compose** | Both skills contribute to the same output | "Design and build a landing page" — design + development together |

**How to detect**: Read the user's request. If it implies a sequence of steps,
those steps can map to different skills. Ask yourself: "Does this request have
multiple phases that different skills could handle?"

**When you detect multi-skill needs**:

1. List the skills involved.
2. Propose the orchestration to the user: "I'll use skill A to read the paper,
   then skill B to write the summary. Sound good?"
3. Execute one skill at a time, passing context between them.

---

## Interaction rules

**Single clear match** → Load immediately. Don't ask.
```
User: "帮我查一下这篇论文"
→ Matches paper-reading (trigger: 论文). Load it.
```

**Multiple matches** → Show options, let user pick.
```
User: "帮我 review 一下代码"
→ code-reviewer (triggers: review) and oracle (description: architecture analysis)
→ "I have two skills for this: code-reviewer (code quality) and oracle
   (architecture review). Which would you like?"
```

**Ambiguous intent** → Ask clarifying questions.
```
User: "帮我把这个改一下"
→ Too vague. Ask: "What kind of change? Fix a bug? Refactor? Add a feature?"
```

**Wrong skill loaded** → Apologize, unload, try the next best match.
```
→ "That wasn't quite the right skill. Let me try another approach..."
```

**Multi-skill detected** → Propose the plan, then execute step by step.
```
→ "This sounds like a pipeline: I'll use paper-reading to read the papers
   first, then thesis-writing to compose the review. Shall I proceed?"
```

---

## Self-maintenance

This SKILL.md doesn't need updating — the routing table is built dynamically
each time. But if you discover a pattern that this file doesn't describe well,
improve it. The process is the product.
