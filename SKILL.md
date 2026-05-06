---
name: skill-router
description: Route freeform user intent to the best matching installed skill. Discovers, matches, and loads skills across all agent platforms.
---

# Skill Router

Route user prompts to the right skill — automatically. If no installed skill
matches, search the community skill ecosystem and install on demand.

Works across Claude Code, WorkBuddy, OpenCode, Gemini CLI, Codex, OpenClaw,
Cursor, and any platform that uses `SKILL.md`.

## When to use

- User says something that sounds like a specific task but doesn't name a skill.
- User doesn't know which skill to use for what they want.
- User wants to do something and you're not sure an installed skill exists for it.
- User mentions a task that spans multiple skills (e.g., "write and review a paper").

**Do NOT use** when the user explicitly names a skill (`/skill-name` or `@skill`).

## How routing works

Read the routing rules below. For each rule, the format is:

`user prompt keywords → action`

Actions are:
- `load:<skill-name>` — Load that skill and follow its instructions.
- `pipeline:<skill-a> → <skill-b>` — Load skill A first, pass its output to skill B.
- `parallel:<skill-a> || <skill-b>` — Load both independently, merge results.
- `compose:<skill-a> + <skill-b>` — Load both, use them together on the same task.
- `ask` — Ask the user clarifying questions to narrow down.
- `search:<query>` — Run `npx skills find "<query>"` and present results.

---

## Global routing table

### Writing & documentation

| When user says... | Route to |
|------------------|----------|
| `write`, `documentation`, `docs`, `README`, `changelog` | `load:content-ops` or `load:copywriting` |
| `commit`, `commit message`, `提交` | `load:ai-git-best-practices` |
| `review my work`, `QA`, `quality check` | `load:content-ops` |
| `remove AI slop`, `humanize`, `去AI味` | `load:humanizer` |
| `copy`, `copywriting`, `marketing copy`, `广告文案` | `load:copywriting` |

### Research & learning

| When user says... | Route to |
|------------------|----------|
| `paper`, `论文`, `research`, `文献`, `arxiv` | `load:arxiv-reader` |
| `tutorial`, `learn`, `teach me`, `讲解`, `介绍` | `compose:open-lesson + peekaboo` |
| `explain`, `what is`, `how does`, `原理` | Use your general knowledge first, then suggest relevant skills |

### Code & development

| When user says... | Route to |
|------------------|----------|
| `code review`, `review code`, `审查代码` | `load:oracle` |
| `debug`, `debugging`, `bug`, `fix`, `错误` | `load:gsd-debug` |
| `refactor`, `重构`, `优化代码` | `load:oracle` |
| `git`, `rebase`, `squash`, `merge` | `load:ai-git-best-practices` |
| `MCP`, `mcp server`, `tool` | `load:mcp-builder` |
| `CLI`, `command line`, `命令行工具` | `load:cli-anything-hub` |

### Design & creative

| When user says... | Route to |
|------------------|----------|
| `design`, `UI`, `UX`, `visual`, `frontend` | `load:canvas-design` or `load:awesome-design-md` |
| `image`, `图片`, `生成图片` | `load:多模态内容生成` |
| `video`, `视频`, `生成视频` | `load:多模态内容生成` |
| `3D`, `3d model`, `模型` | `load:多模态内容生成` |

### Data & analysis

| When user says... | Route to |
|------------------|----------|
| `excel`, `spreadsheet`, `xlsx`, `csv`, `表格` | `load:xlsx` |
| `word`, `docx`, `文档`, `报告` | `load:docx` |
| `ppt`, `powerpoint`, `slides`, `演示`, `slides` | `load:pptx` |
| `pdf` | `load:pdf` or `load:pdfkit-py` |

### Workflow & productivity

| When user says... | Route to |
|------------------|----------|
| `plan`, `project`, `milestone`, `roadmap`, `规划` | `load:gsd-new-project` or `load:gsd-progress` |
| `task`, `todo`, `待办`, `任务` | `load:gsd-check-todos` |
| `automation`, `schedule`, `cron`, `定时`, `自动` | `load:automation-workflows` |
| `goal`, `goals`, `目标`, `track`, `追踪` | `load:goal-tracker` |

### Content operations

| When user says... | Route to |
|------------------|----------|
| `social media`, `linkedin`, `twitter`, `小红书` | `load:social-content` or `load:xiaohongshu` |
| `email`, `newsletter`, `邮件` | `load:email-sequence` |
| `blog`, `post`, `article`, `文章` | `load:content-ops` |
| `SEO`, `search engine`, `搜索优化` | `load:seo-audit` or `load:programmatic-seo` |

### System & platform

| When user says... | Route to |
|------------------|----------|
| `web search`, `search`, `查找`, `搜索` | `load:web-scraper` or `load:multi-search-engine` |
| `browser`, `网页`, `website`, `截图` | `load:agent-browser` |
| `github`, `pr`, `issue`, `pull request` | `load:github` |
| `security`, `安全`, `scan`, `vulnerability` | `load:skill-scanner` |

---

## Multi-skill patterns

These prompts span multiple skills. Route them as a unit.

| When user says... | Route |
|------------------|-------|
| `write and publish` | `pipeline:copywriting → social-content` |
| `research then write` | `pipeline:arxiv-reader → content-ops` |
| `design and build` | `pipeline:awesome-design-md → canvas-design` |
| `review and fix` | `pipeline:oracle → gsd-debug` |
| `read and summarize` | `pipeline:arxiv-reader → content-ops` |
| `write and review` | `pipeline:copywriting → content-ops` |
| `analyze and visualize` | `pipeline:xlsx → canvas-design` |
| `查 GitHub 趋势和新闻` | `parallel:github-trending-cn || multi-search-engine` |
| `写论文综述` | `pipeline:arxiv-reader → content-ops` |

---

## Platform-aware skill discovery

When you need to find a skill, check these locations in order:

1. **Project-level** — `.claude/skills/<name>/SKILL.md` or `.workbuddy/skills/<name>/SKILL.md`
2. **User-level** — `~/.claude/skills/<name>/SKILL.md` or `~/.workbuddy/skills/<name>/SKILL.md`
3. **Universal** — `~/.agents/skills/<name>/SKILL.md`
4. **Other platforms** — `~/.config/opencode/skills/`, `~/.gemini/skills/`, `.cursor/skills/`, etc.

**Precedence:** Project-level skills override user-level skills with the same name.

---

## Fallback: network search

If no installed skill matches the user's intent:

1. Run: `npx skills find "<describe what the user wants in 5-10 English words>"`
2. Read the results. Present up to 3 options to the user.
3. If the user wants to install one: `npx skills add <owner/repo@skill> -g -y`
4. After installation, the skill is available for future routing.

---

## Self-maintenance

This routing table is meant to grow. When you discover a new routing pattern:

1. **Add a new row** to the appropriate table in this file.
2. Use the user's exact keywords so the pattern is clear.
3. If the skill comes from a new platform, add it to the discovery paths.
4. Commit the update if you have write access to the skill file.

When you encounter a prompt that clearly needs multiple skills:

1. **Add a new row** to the multi-skill patterns table.
2. Specify the relationship: `pipeline`, `parallel`, or `compose`.

---

## Interaction rules

- **When multiple skills match at similar strength**: Show the user the options
  and ask which they prefer. Example: "I can review your code with oracle (for
  architecture review) or gsd-debug (for bug hunting). Which would you like?"

- **When a single skill clearly matches**: Load it immediately. Don't ask.

- **When you loaded a skill and it wasn't the right one**: Unload it, tell the
  user "that wasn't quite right", and either try another match or ask for
  clarification.

- **When you don't know what to do with the result**: Be honest. Say "I've
  loaded the skill but I'm not sure this is what you wanted. Can you clarify?"
