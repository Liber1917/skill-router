---
name: skill-router
description: "自动帮你在已安装的 200+ 技能中找到最合适的一个。说一句话，它替你挑 skill——写论文、查 GitHub、读文献、做 PPT，自动匹配。支持多技能串联/并行编排，找不到还能自动搜索 skills.sh 安装。所有路由行为带 [skill-router] 审计前缀。"
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
[skill-router] ┌─ ENTRY GUARD ─→ SCAN ─→ MATCH ─→ LOAD GUARD ─→ Load skill ─→ VERIFY HOOK ─→ CONTROL HOOK ─┐
[skill-router] └────────────────────────── persistent loop ────────────────────────────────────────────────┘
```

Works across Claude Code, WorkBuddy, OpenCode, Gemini CLI, Codex, OpenClaw,
Cursor, and any platform that uses `SKILL.md`.

---

## 1. ENTRY GUARD — ROUTE OR CHAT?

**FIRST thing you do when this skill is loaded.** Before any scan, any match —
decide: does this user message need routing at all?

If the user is clearly just chatting:
- Greetings ("你好", "hello")
- Simple factual questions ("Python 怎么排序", "今天天气")
- Casual conversation
→ Exit router. Do NOT prefix anything. Reply normally.

If the user describes a task, names a domain, or asks "帮" + verb:
→ Enter SCAN phase.

**Rule**: When in doubt, route. False positives waste 5 seconds. False
negatives miss the right skill entirely.

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

### Cross-Domain Detection (run after scoring)

Before presenting results, check for multi-intent signals:

**Linguistic signals** (user expresses ≥2 intents):
- Chinese: "又...又...", "既要...又要...", "和", "还有", "然后", "之后"
- English: "and also", "plus", "then", "after that", "first...then"

**Candidate signals** (matches span different domains):
- ≥2 candidates with scores in [0.5, 0.85] range
- OR ≥2 High candidates from different domains
- Candidate `tags` have NO intersection → different domains

**Decision**:
- `cross_domain = true` → BOTH signal types present
- `cross_domain = possible` → only linguistic signal detected
- Record candidate list for Section 4

**CRITICAL**: Do NOT invent skills. Do NOT guess. If not found → fallback.

---

## 4. LOAD GUARD — VERIFY BEFORE LOADING

After match, **do NOT load anything yet**. Pass through this guard:

| Match | Guard action |
|-------|-------------|
| **High** | Announce. Load immediately. |
| **Medium** | Present options. User MUST pick. |
| **Medium + cross_domain=true** | Present options + pipeline/compose suggestion (Section 9). |
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

## 7. CONTROL HOOK — PERSISTENT SESSION WITH BOUNDARY GUARD

After route + execution, the router stays active — but **does not re-route silently**.
A BOUNDARY GUARD runs on each new user message:

```
New message
    │
    ▼
┌──────────────────────────────────────────┐
│  BOUNDARY GUARD                          │
│  Match msg ↔ current skill domain        │
├──────────────────────────────────────────┤
│  ≥0.85  → stay silent, pass thru         │
│  <0.85  → is user asking for a skill?    │
│    ├ YES (帮/找/推荐skill/which/路由) → ask│
│    └ NO → stay silent, pass thru         │
└──────────────────────────────────────────┘
```

**Critical: BOUNDARY GUARD is silent by default.** It only speaks when
the user literally asks for routing help. This avoids wasting context
turns on "do you need a skill?" noise in long-running sessions.

**Rules**:
- **≥0.85 (same thread)** → Stay silent. Pass through. Never mention routing.
- **<0.85 + user asks for skill** ("帮我找 sdkill", "推荐 skill", "有XX技能吗", "which skill", "路由") → Ask once: `[skill-router] 需要我帮你找合适的 skill 吗？`
  - Confirms → Enter SCAN → MATCH → LOAD GUARD.
  - Declines → Pass through. This session's BOUNDARY GUARD is suppressed.
- **<0.85 + user does NOT ask for skill** → Stay silent. Pass through. Do NOT ask.
- **CRITICAL**: Do NOT re-route automatically. Do NOT ask unprompted. The BOUNDARY GUARD is a **listener with a hotkey**, not a greeter.

---

## 8. OUTPUT FORMAT — GREP-ABLE CONTRACT

Every route step **MUST** prefix with `[skill-router]`. Example:

```
[skill-router] Entry: wants routing — task detected
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
[skill-router] Entry: wants routing — multi-domain
[skill-router] Scan: 46 skills
[skill-router] Match: pipeline detected — paper-reading → thesis-writing
[skill-router] Load Guard: Proposing pipeline to user
```

---

## 9. MULTI-SKILL ROUTING

**When to propose** (triggered from Section 4 when `cross_domain=true`):

Present user with a concise choice **in 1 round**:

```
[skill-router] 检测到多领域需求，请选择执行方式：
  1. Pipeline（顺序执行）：A 完成后，将结果传给 B
  2. Compose（组合执行）：A 和 B 同时使用，各自处理任务的不同部分
  3. 单独执行某个技能（{list individual skills}）
```

**Patterns**:

| Pattern | When to use | Execution |
|---------|--------------|-------------|
| **Pipeline (A → B)** | User says "先...再...", "然后", "step by step" | Load A → run → capture output → load B with output → VERIFY at end |
| **Compose (A + B)** | User says "同时", "一起", domains are independent | Load both → run together → merge outputs → VERIFY |
| **Parallel (A ∥ B)** | User wants independent results merged | Load both → run independently → merge → VERIFY |

**Execution rules**:
1. Execute ONE skill at a time (no parallel API calls)
2. Pass context explicitly: "A 的输出是：{output}. 现在用 B 处理。"
3. After all skills run → VERIFY HOOK with combined output
4. If user picks "单独执行" → fall back to normal single-skill load

**CRITICAL**: Never auto-execute multi-skill without user confirmation. Always present the plan first.

---

## 10. LOGGING (OPT-IN)

If the user has given explicit consent:
Append a JSONL line to `~/.skill-router/log.jsonl` after each route:

```jsonl
{"ts":"2026-05-07T09:00:00","prompt":"帮我写论文","matched":"paper-reading","score":0.92,"verify":"success"}
```

**Do NOT log without asking the user first.**
When asked, explain: "This logs routing outcomes locally to measure accuracy.
No data leaves your machine. Opt in?"

---

## 11. COMPLIANCE CHECKLIST

| # | Check | Pass |
|---|-------|------|
| 1 | Did I pass ENTRY GUARD (route or chat)? | ☐ |
| 2 | Did I SCAN actual directories (not guess)? | ☐ |
| 3 | Did I compare against ALL scanned skills? | ☐ |
| 4 | Did I pass LOAD GUARD before loading? | ☐ |
| 5 | Did I prefix every output with `[skill-router]`? | ☐ |
| 6 | Did I run VERIFY HOOK after the skill finished? | ☐ |
| 7 | Did I run BOUNDARY GUARD before re-routing or staying silent? | ☐ |

**If any box is unchecked, you skipped a step. Fix it.**
