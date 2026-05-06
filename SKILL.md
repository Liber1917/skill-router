---
name: skill-router
description: "CRITICAL ROUTING SKILL: Scan, discover, and route user intent to the best matching installed skill. Dynamic routing from your actual skills — no hardcoded rules."
triggers:
  - route
  - 路由
  - 不知道用什么技能
  - 有什么skill
  - which skill
  - skill推荐
  - skill routing
  - 自动匹配技能
  - 帮我找skill
  - 推荐skill
---

# Skill Router — MUST READ BEFORE ROUTING

**CRITICAL: This is a meta-skill. It does NOT do work itself. Its only job
is to find the right skill and hand off. You MUST execute all three phases
below, in order, every time. No shortcuts. No guessing.**

```
User request
  → Phase 1: SCAN (discover installed skills)
  → Phase 2: MATCH (compare against user intent)
  → Phase 3: ACT (invoke, propose, or fallback)
  → Outcome + handoff
```

**If you skip a phase**, the user will get wrong results and lose trust.
**If you guess instead of scanning**, you will route to skills that don't
exist. **You must follow the process.**

Works across Claude Code, WorkBuddy, OpenCode, Gemini CLI, Codex, OpenClaw,
Cursor, and any platform that uses `SKILL.md`.

---

## PHASE 1: SCAN — DISCOVER ALL SKILL FILES

**This is mandatory. You MUST NOT skip this phase.**

Read every `SKILL.md` you can find. For each skill, extract three fields:
**name**, **description**, and **triggers** (from YAML frontmatter only).

Check these locations **in this order**:

| Priority | Level | Paths |
|----------|-------|-------|
| **1st** | **Project** | `.claude/skills/*/SKILL.md`, `.workbuddy/skills/*/SKILL.md`, `.opencode/skills/*/SKILL.md`, `.gemini/skills/*/SKILL.md`, `.codex/skills/*/SKILL.md`, `.openclaw/skills/*/SKILL.md`, `.cursor/skills/*/SKILL.md`, `.agents/skills/*/SKILL.md` |
| **2nd** | **User** | `~/.claude/skills/*/SKILL.md`, `~/.workbuddy/skills/*/SKILL.md`, `~/.config/opencode/skills/*/SKILL.md`, `~/.gemini/skills/*/SKILL.md`, `~/.codex/skills/*/SKILL.md`, `~/.openclaw/skills/*/SKILL.md`, `~/.agents/skills/*/SKILL.md` |

### Rules

- **If the same skill name exists at both project and user level**: prefer
  the project-level one (it's more context-specific).
- **If a directory doesn't exist**: skip it silently. No warnings.
- **If a SKILL.md has no frontmatter**: use the directory name as fallback.
- **Do NOT scan** hidden directories (`.git/`, `__pycache__/`, `.venv/`, etc.).
- **You MUST list what you found** in your response — show the count and the
  platforms. Example: `"Scanned 46 skills across 3 platforms (WorkBuddy,
  Claude Code, Universal agents)."`

---

## PHASE 2: MATCH — EVALUATE EACH SKILL

**This is mandatory. You MUST compare the user's request against EVERY
scanned skill. Do NOT cherry-pick.**

Compare the user's request against each skill's **name**, **description**,
and **triggers** field.

### Confidence Levels

| Level | Condition | Action |
|-------|-----------|--------|
| **High (≥0.85)** | User's words match a skill's triggers exactly, OR name/description is an unambiguous match | Load the skill immediately. Do not ask. |
| **Medium (0.5–0.85)** | Semantic match but not exact (e.g., user says "文献" and skill triggers don't include it, but description mentions "academic papers") | **MUST show the user** at least 2 options with scores. Let them pick. |
| **Low (<0.5)** | Multiple skills partially match | Show all candidates. Ask clarifying questions. |
| **No match** | No skill matches the user's intent at all | Go to Phase 3. |

### CRITICAL RULES

- **You MUST NOT guess skill names or descriptions.** You read them from the
  actual SKILL.md files in Phase 1. If you didn't find a file for it, it
  doesn't exist.
- **You MUST NOT invent skills.** If no installed skill matches, go to Phase 3.
  Do not pretend a skill exists.
- **You MUST present the confidence scores.** Show the user why you chose
  one skill over another.
- **Low confidence means you ask.** If you're not sure, ask. Never silently
  pick the wrong one.

---

## PHASE 3: ACT — INVOKE, PROPOSE, OR FALL BACK

Based on Phase 2's result, take one of these actions:

### Action A: Single clear match (high confidence)

1. Announce which skill you found and why.
2. **Load the skill** and follow its instructions.
3. After the skill finishes, return to the user.

**You MUST NOT ask for confirmation** when confidence is high. Just do it.

### Action B: Multiple matches (medium/low confidence)

1. Present the candidates with scores and reasoning.
2. **Let the user pick.**
3. Load the chosen skill.

### Action C: No match (fallback)

1. Run: `npx skills find "<describe the user's need in 5-10 English words>"`
2. Read the results. Select the most relevant 1-3 options.
3. Present them to the user with name, description, and install command.
4. If the user wants to install: `npx skills add <owner/repo@skill> -g -y`
5. After install, the skill is immediately available.

If `npx` is not available: suggest searching manually at
https://skills.sh or https://github.com/topics/agent-skills.

---

## MULTI-SKILL ROUTING

Some requests need multiple skills working together. Detect these patterns:

| Pattern | Meaning | Example |
|---------|---------|---------|
| **Pipeline** | A → B (A's output feeds B) | "Read paper then write summary" |
| **Parallel** | A \|\| B (independent) | "Check GitHub trends AND search news" |
| **Compose** | A + B (both contribute) | "Design AND build landing page" |

**How to detect**: Ask "Does this request have multiple phases that different
skills could handle?" If yes, propose the orchestration plan to the user.

**CRITICAL**: Execute one skill at a time. Do NOT load all skills at once.
Pass context between them explicitly.

---

## OUTPUT FORMAT — YOU MUST FOLLOW THIS

Every time you route, you **MUST** present the result in this exact format.
Do not omit phases. Do not merge them.

### Single match
```
**Phase 1: Scan** ✅ — N skills across M platforms

**Phase 2: Match** — "{user prompt}"
→ Single high-confidence match found

| Skill | Confidence | Reason |
|-------|-----------|--------|
| name | high ~0.95 | trigger/description matched "{keyword}" |

**Result**: Loading [name]. [Brief summary of what it does.]
```

### Multiple matches
```
**Phase 1: Scan** ✅ — N skills

**Phase 2: Match** — "{user prompt}"
→ Multiple candidates

| Skill | Confidence | Reason |
|-------|-----------|--------|
| skill-a | 0.75 | reason |
| skill-b | 0.60 | reason |

**Result**: Which one would you like to use?
```

### No match
```
**Phase 1: Scan** ✅ — N skills

**Phase 2: Match** — "{user prompt}"
→ No match found among installed skills.

**Phase 3: Fallback** — searching skills.sh...
→ Found "some-skill" (description). Install it?
```

---

## INTERACTION RULES

- **High confidence**: Load immediately. Do not ask.
- **Medium/low confidence**: Show options. Let user pick.
- **Ambiguous intent**: Ask clarifying questions before routing.
- **Wrong skill loaded**: Unload immediately. Say "That wasn't right."
  Try next best match or ask for clarification.
- **Multi-skill detected**: Propose plan. Execute step by step.
- **User names a skill explicitly** (`/name` or `@name`): **Do NOT use this
  skill.** The user already knows what they want.

**CRITICAL**: If you loaded a skill and it completes, return to the user.
Do not start another routing cycle unless the user asks.

---

## WHY THIS PROCESS MATTERS

- **If you skip Phase 1**: You will route to skills that don't exist.
- **If you skip Phase 2 scoring**: The user won't know why you chose what
  you chose.
- **If you skip Phase 3**: The user gets "nothing found" without options.
- **If you skip the output format**: The user can't follow what happened.

**Follow the phases. Every time. No exceptions.**
