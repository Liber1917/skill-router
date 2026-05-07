---
name: skill-router
description: "CRITICAL: Route user intent to the best matching installed skill via dynamic cross-platform scan. Uses triage + scan + match + guard hook lifecycle. Audit trail via [skill-router] prefix."
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

# Skill Router — LIFECYCLE (MUST FOLLOW)

**CRITICAL: This is a meta-skill. It does NOT do work itself. It routes.**

**Every output line from this skill MUST be prefixed with `[skill-router]`.**
This makes the audit trail grep-able across sessions.
`grep '\[skill-router\]'` in any transcript to see what fired.

```
[skill-router] ┌── Triage ──→ SCAN ──→ Match ──→ Guard ──→ Load ──→ Verify ──→ Control ──┐
[skill-router] └──────────────────────── persistent loop ────────────────────────────────┘
```

Works across Claude Code, WorkBuddy, OpenCode, Gemini CLI, Codex, OpenClaw,
Cursor, and any platform that uses `SKILL.md`.

---

## 1. TRIAGE — 3-QUESTION CLASSIFIER

Before any scan, classify the user request with 3 questions.
**Run this in <2 seconds. Prefix every line with `[skill-router]`.**

```
[skill-router] Q1: Is something BROKEN / WRONG / FAILING?
              Error, crash, test fail, unexpected behavior, user correction
              YES → needs a debugging/correction skill → mark as [FIX]

[skill-router] Q2: Is this CREATE / BUILD / ADD something new?
              New feature, file, component, integration, project
              YES → needs a creation skill → mark as [BUILD]

[skill-router] Q3: Everything else (improve, ship, configure, automate, research)
              → mark as [OPERATE]
```

**Rule**: AMBIGUOUS? → Default to [OPERATE]. Never skip triage entirely.

**If the user is clearly just chatting** (greeting, simple question, no task):
→ Exit router. Do NOT prefix anything. Reply normally.

---

## 2. SCAN — DISCOVER ALL INSTALLED SKILLS

**This is mandatory. You MUST NOT skip this phase.**

Read every `SKILL.md` you can find. Extract **name**, **description**, and
**triggers** from YAML frontmatter.

Check these locations **in order**:

| Priority | Level | Paths |
|----------|-------|-------|
| **1st** | **Project** | `.claude/skills/*/SKILL.md`, `.workbuddy/skills/*/SKILL.md`, `.opencode/skills/*/SKILL.md`, `.gemini/skills/*/SKILL.md`, `.codex/skills/*/SKILL.md`, `.openclaw/skills/*/SKILL.md`, `.cursor/skills/*/SKILL.md`, `.agents/skills/*/SKILL.md` |
| **2nd** | **User** | `~/.claude/skills/*/SKILL.md`, `~/.workbuddy/skills/*/SKILL.md`, `~/.config/opencode/skills/*/SKILL.md`, `~/.gemini/skills/*/SKILL.md`, `~/.codex/skills/*/SKILL.md`, `~/.openclaw/skills/*/SKILL.md`, `~/.agents/skills/*/SKILL.md` |

**Rules**:
- Same-name skills: project-level wins over user-level.
- Missing dir: skip silently.
- No frontmatter: dir name as fallback.
- **Do NOT scan** hidden dirs (`.git/`, `__pycache__/`, etc.).
- Report: `[skill-router] Scanned {N} skills across {M} platforms: {list}.`

---

## 3. MATCH — COMPARE AGAINST USER INTENT

Compare the user's request against each scanned skill's **name**, **description**,
and **triggers**.

| Level | Condition | Action |
|-------|-----------|--------|
| **High (≥0.85)** | Exact trigger match or unambiguous semantic match | Load immediately. **Do NOT ask.** |
| **Medium (0.5–0.85)** | Semantic match, not exact | Show ≥2 options with scores. Let user pick. |
| **Low (<0.5)** | Multiple partial matches | Show all. Ask clarifying questions. |
| **No match** | Nothing relevant | Go to network fallback. |

**CRITICAL**: Do NOT invent skills. Do NOT guess. If not found → fallback.

---

## 4. LOAD GUARD — VERIFY BEFORE LOADING

After match, **do NOT load anything yet**. Pass through this guard:

| Match | Guard action |
|-------|-------------|
| **High** | Announce. Load immediately. |
| **Medium** | Present options. User MUST pick. |
| **Low** | Ask clarifying. Re-match. |
| **None** | Network fallback. |

If error: call VERIFY HOOK → failure path.

---

## 5. NETWORK FALLBACK

If no installed skill matches:

1. `npx skills find "<describe need in 5-10 English words>"`
2. Present up to 3 options with name + description + install command.
3. User confirms → `npx skills add <owner/repo@skill> -g -y`
4. After install, skill is immediately available.

If `npx` not available → suggest skills.sh or GitHub.

---

## 6. VERIFY HOOK — CHECK EXECUTION RESULT

After the loaded skill finishes:

**Success**: Output matches user intent.
→ `[skill-router] Verify: ✅ {skill} completed correctly`
→ Move to CONTROL HOOK.

**Failure**: Output off-topic, wrong, or incomplete.
→ `[skill-router] Verify: ❌ {skill} — result didn't match`
→ Unload. Return to SCAN for next candidate.
→ If 2 consecutive failures: ask user for clarification.

---

## 7. CONTROL HOOK — PERSISTENT SESSION

After route + execution, the router stays active:

- **Same thread** → Stay in loaded skill. No re-route.
- **New thread** → Re-enter TRIAGE → SCAN → MATCH → GUARD.
- **Uncertain** → Default to re-scan.

---

## 8. OUTPUT FORMAT — GREP-ABLE CONTRACT

Every route step **MUST** prefix with `[skill-router]`. Example:

```
[skill-router] Triage: [BUILD] user wants to create something
[skill-router] Scan: 46 skills across 3 platforms
[skill-router] Match: paper-reading (high ~0.92) — trigger "论文" matches
[skill-router] Load Guard: Passed (≥0.85)
[skill-router] Verify: ✅ paper-reading completed correctly
[skill-router] Control: waiting — thread active
```

**Failure format**:
```
[skill-router] Match: no match found
[skill-router] Fallback: searching skills.sh...
[skill-router] Found "thesis-writer" (write academic papers). Install?
```

**Multi-skill format**:
```
[skill-router] Triage: [BUILD] multi-domain detected
[skill-router] Scan: 46 skills
[skill-router] Match: pipeline detected — paper-reading → thesis-writing
[skill-router] Load Guard: Proposing pipeline to user
```

---

## 9. MULTI-SKILL ROUTING

| Pattern | Action |
|---------|--------|
| **Pipeline (A → B)** | Load A, run, load B with A's output, VERIFY at end |
| **Parallel (A ∥ B)** | Load both, run independently, merge |
| **Compose (A + B)** | Load both, use together on same task |

CRITICAL: Execute one at a time. Pass context between steps.

---

## 10. LOGGING (OPT-IN)

If the user has given explicit consent:
Append a JSONL line to `~/.skill-router/log.jsonl` after each route:

```jsonl
{"ts":"2026-05-07T09:00:00","triage":"BUILD","prompt":"帮我写论文","matched":"paper-reading","score":0.92,"verify":"success"}
```

**Do NOT log without asking the user first.**
When asked, explain: "This logs routing outcomes locally to measure accuracy.
No data leaves your machine. Opt in?"

---

## 11. COMPLIANCE CHECKLIST

| # | Check | Pass |
|---|-------|------|
| 1 | Did I run TRIAGE (3 questions)? | ☐ |
| 2 | Did I SCAN actual directories (not guess)? | ☐ |
| 3 | Did I compare against ALL scanned skills? | ☐ |
| 4 | Did I pass LOAD GUARD before loading? | ☐ |
| 5 | Did I prefix every output with `[skill-router]`? | ☐ |
| 6 | Did I run VERIFY HOOK after the skill finished? | ☐ |
| 7 | Did I enter CONTROL HOOK? | ☐ |

**If any box is unchecked, you skipped a step. Fix it.**
