---
name: skill-router
description: "CRITICAL ROUTING SKILL: Scan, discover, and route user intent to the best matching installed skill. Dynamic routing from your actual skills — no hardcoded rules. This skill uses a hook-based lifecycle: ENTRY GUARD → SCAN → MATCH → LOAD GUARD → VERIFY HOOK → CONTROL HOOK."
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

The router is a **lifecycle with guard hooks at every boundary**. You do not
"run the router once and forget it" — you enter a persistent routing loop
that checks, loads, verifies, and re-enters on every user message.

```
┌────────────────────────────────────────────────────┐
│  [ENTRY GUARD]     用户想路由还是直接聊?            │
│    ├ 不想路由 → 退出, 正常回复                       │
│    └ 需要路由 → 进入 SCAN                           │
├────────────────────────────────────────────────────┤
│  Phase 1: SCAN    发现所有已安装 skill               │
├────────────────────────────────────────────────────┤
│  Phase 2: MATCH   对比用户意图                       │
├────────────────────────────────────────────────────┤
│  [LOAD GUARD]     匹配结果可信吗?                    │
│    ├ high → 直接加载                                │
│    ├ med  → 展示选项                                 │
│    ├ low  → 追问                                    │
│    └ none → 网络回退                                │
├────────────────────────────────────────────────────┤
│  [VERIFY HOOK]    skill 执行完, 结果对吗?            │
│    ├ 对 → 汇报                                      │
│    └ 错 → 卸载, 回到 SCAN                           │
├────────────────────────────────────────────────────┤
│  [CONTROL HOOK]   用户下一条消息                     │
│    ├ 同主题 → 留在当前 skill                         │
│    └ 新主题 → 回到 ENTRY GUARD                      │
└────────────────────────────────────────────────────┘
```

**Every user message enters this cycle. No exceptions. No "one-shot" mode.**

---

## [ENTRY GUARD] — Confirm routing is needed

**FIRST thing you do when this skill is loaded.** Before any scan, before any
match — check if the user actually needs routing.

```
User says: "帮我查一下 GitHub 仓库"
→ Heuristic: contains "帮我" + describes a task. This wants a skill. → Proceed.

User says: "今天天气怎么样"
→ Heuristic: simple factual question. No skill needed. → Exit router, answer directly.

User says: "你好"
→ Clear social greeting. → Exit router, respond normally.
```

**Heuristics to decide** (use your judgment, not keyword matching):

| Signal | Wants routing | Does NOT want routing |
|--------|--------------|----------------------|
| User describes a *task* | ✅ "帮我写论文" | ❌ "今天天气" |
| User names a *domain* | ✅ "GitHub 上的 issue" | ❌ "你好" |
| User asks a *simple factual question* | ❌ "Python 怎么排序" | ✅ exit |
| User continues previous conversation | ❌ depends | use CONTROL HOOK |
| User explicitly says "帮" + verb | ✅ always | — |

**If unsure**: ask. "I can route this to a skill or just answer directly.
Which would you prefer?"

**CRITICAL**: False positives (routing when not needed) are wasted time.
False negatives (not routing when needed) are worse. When in doubt, route.

---

## Phase 1: SCAN — mandatory

Same as current. Read all skill directories. Report count + platforms.
**You MUST NOT skip this phase.**

---

## Phase 2: MATCH — mandatory

Same as current. Compare every scanned skill against user intent.
**You MUST NOT cherry-pick.**

---

## [LOAD GUARD] — Verify before loading

After Phase 2 produces a result, **do NOT load anything yet**. First pass
through this guard:

| Match result | Guard action |
|-------------|--------------|
| **High (≥0.85)** | Announce the match. Load immediately. **Do NOT ask.** |
| **Medium (0.5–0.85)** | Present options with scores. **User MUST pick.** |
| **Low (<0.5)** | Ask clarifying questions. Re-match if needed. |
| **No match** | Go to Phase 3 (network fallback). |

**CRITICAL**: If you loaded a skill in error, you MUST call
`[VERIFY HOOK] → failure path`. Do NOT silently continue with the wrong skill.

---

## [VERIFY HOOK] — Check the result

After the loaded skill finishes executing, check whether it actually worked.

**Success signal**: The skill's output matches what the user asked for.
→ Report results to the user.
→ Move to CONTROL HOOK.

**Failure signal**: The skill's output is off-topic, incomplete, or wrong.
→ Say "That wasn't the right skill for this."
→ **Unload the skill immediately.**
→ Return to Phase 1 (re-scan) and try again.
→ If this happens twice in a row, ask the user: "I've tried two skills and
  neither seems right. Can you describe what you need differently?"

**You MUST NOT** let a wrong skill keep running. Unload on first mismatch.

---

## [CONTROL HOOK] — Wait for next user message

After a successful route + execution, the router stays active. Each new
user message runs through the ENTRY GUARD again:

- **Same thread** — User asks a follow-up about the same topic.
  Stay in the loaded skill. Do not re-route.

- **New thread** — User shifts to a completely different topic.
  Re-enter ENTRY GUARD → SCAN → MATCH → LOAD GUARD.

- **Uncertain** — You can't tell if it's the same thread or a new one.
  Re-scan and propose. It costs nothing to check.

**Example of correct cycle:**

```
User: "帮我检查 GitHub 仓库"
  → ENTRY GUARD: "帮我" + task → wants routing
  → SCAN: 46 skills
  → MATCH: github (high 0.9)
  → LOAD GUARD: high conf, loading...
  → github skill runs → VERIFY: correct results
  → CONTROL HOOK: waiting...

User: "那再帮我看看论文"
  → ENTRY GUARD: new topic (论文 ≠ GitHub) → wants routing
  → SCAN: 46 skills (re-scan, might have changed)
  → MATCH: arxiv-reader (high 0.85)
  → LOAD GUARD: loading...
  → ...
```

---

## MULTI-SKILL ROUTING

Some requests need multiple skills. Handle them at the MATCH stage:

| Pattern | What to do |
|---------|-----------|
| **Pipeline** (A → B) | Load A, run, load B with A's output, run, VERIFY at end |
| **Parallel** (A ∥ B) | Load both, run independently, merge results |
| **Compose** (A + B) | Load both, use together on same task |

**CRITICAL**: Execute one at a time. Pass context between them. Do NOT load
all at once.

---

## OUTPUT FORMAT — YOU MUST FOLLOW THIS

Every route attempt **MUST** produce this format. No exceptions.

### Successful route (high confidence)
```
**Phase 1: Scan** ✅ — {N} skills across {M} platforms

**Phase 2: Match** — "{user prompt}"
→ Single high-confidence match

| Skill | Confidence | Reason |
|-------|-----------|--------|
| {name} | high ~{score} | {trigger field matched "{keyword}"} |

**Load Guard**: Passed (≥0.85)
**Result**: Loading {name}. {brief description}
```

### Multiple candidates (medium/low)
```
**Phase 1: Scan** ✅ — {N} skills

**Phase 2: Match** — "{user prompt}"
→ Multiple candidates

| Skill | Confidence | Reason |
|-------|-----------|--------|
| {a} | {0.75} | {reason} |
| {b} | {0.60} | {reason} |

**Load Guard**: Medium confidence — Which one would you like to use?
```

### Fallback (no match)
```
**Phase 1: Scan** ✅ — {N} skills

**Phase 2: Match** — "{user prompt}"
→ No match found

**Phase 3: Fallback** — searching skills.sh...
→ Found "{skill-name}" ({description}). Install it?
```

### Verify hook failure
```
**Verify Hook**: ❌ — Loaded {skill} but result doesn't match what user asked.

Unloading {skill}. Re-entering Phase 1...

**Phase 1: Scan** ✅ — re-scanning...
**Phase 2: Match** — trying next candidate...
```

---

## COMPLIANCE CHECKLIST

Before you respond to any user message while this skill is loaded, verify:

| # | Check | Pass |
|---|-------|------|
| 1 | Did I pass through ENTRY GUARD? | ☐ |
| 2 | Did I scan actual skill directories (not guess)? | ☐ |
| 3 | Did I compare against ALL scanned skills? | ☐ |
| 4 | Did I pass through LOAD GUARD before loading? | ☐ |
| 5 | Did I run VERIFY HOOK after the skill finished? | ☐ |
| 6 | Did I enter CONTROL HOOK after the conversation? | ☐ |

**If any box is unchecked, you skipped a step. Fix it before responding.**

---

## WHY THIS LIFECYCLE MATTERS

| Skip this | Consequence |
|-----------|-------------|
| ENTRY GUARD | You route when user just wants a chat |
| Phase 1 (SCAN) | You guess skills that don't exist |
| Phase 2 (MATCH) | You pick the wrong skill |
| LOAD GUARD | You load before user confirms |
| VERIFY HOOK | Wrong skill keeps running silently |
| CONTROL HOOK | Router is lost after one use |
