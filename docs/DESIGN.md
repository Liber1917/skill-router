# skill-router 设计文档

**日期**: 2026-05-06
**状态**: 已批准 ✅
**后续**: 用户审阅 → 批准 → 创建仓库 → 实现

---

## 1. 概述

### 要解决什么问题
用户说一句话（自然语言），skill-router 自动找到最匹配的 skill 并执行。如果本地没有匹配，搜索社区 skill 生态并提出安装。

### 不是什么
- 不是 agent-skill-infra 的一部分（独立仓库）
- 不是 skill 执行引擎（只做路由，不做执行）
- 不是 GSD（不绑定任何项目或工作流）
- 不是 oh-my-openagent（不负责模型选择或 agent 编排）

### 一句话定位
**A cross-platform natural language router for agent skills — finds the right skill wherever it lives.**

---

## 2. 架构

### 2.1 跨平台 skill 来源

skill-router 的核心差异化：**平台无关**。它扫描所有主流 agent 平台的技能目录，而不仅限 WorkBuddy。

#### 已知平台注册表

| 平台 | 用户级路径 | 项目级路径 | 备注 |
|------|-----------|-----------|------|
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` | 也扫描嵌套子目录的 `.claude/skills/` |
| **WorkBuddy** | `~/.workbuddy/skills/` | `.workbuddy/skills/` | |
| **OpenCode** | `~/.config/opencode/skills/` | `.opencode/skills/` | 也扫描 `.claude/` 和 `.agents/` 兼容 |
| **OpenClaw** | `~/.openclaw/skills/` | `.openclaw/skills/` | SKILL.md 格式与 Claude Code 完全兼容 |
| **Gemini CLI** | `~/.gemini/skills/` | `.gemini/skills/` | 也扫描 `~/.agents/skills/` 和 `.agents/skills/` |
| **Codex CLI** | `~/.codex/skills/` | `.codex/skills/` | 同格式 |
| **Cursor** | (无) | `.cursor/skills/` | 仅项目级 |
| **Universal** | `~/.agents/skills/` | `.agents/skills/` | OpenCode + Gemini CLI 通用的跨平台别称 |

#### 扫描流程

```
user prompt
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  auto-detect platforms                               │
│  ├ 遍历平台注册表, 检查哪些路径存在                   │
│  ├ 允许用户通过 config 添加自定义平台                  │
│  ├ 检测到路径 → 注册该平台的 skill 扫描器             │
│  └ 示例: 检测到 ~/.claude/skills/ → 激活 Claude 扫描  │
├─────────────────────────────────────────────────────┤
│  scan all skill directories (project → user)          │
│  ├ 先扫描项目级路径 (所有已激活平台的)                 │
│  ├ 再扫描用户级路径 (所有已激活平台的)                 │
│  ├ 每个 skill 标记来源平台 + 层级                      │
│  └ 相同 name 时: 项目级 > 用户级 (可配置)              │
├─────────────────────────────────────────────────────┤
│  index: skill metadata pool                           │
│  ├ 每个 skill 包含: name, desc, triggers, platform     │
│  ├ 层级: "project" | "user"                           │
│  └ 来源: "claude" | "workbuddy" | "opencode" | ...   │
├─────────────────────────────────────────────────────┤
│  network-level (fallback)                             │
│  └ 本地无匹配时搜索 skills.sh / GitHub                 │
└─────────────────────────────────────────────────────┘
```

#### 优先级规则

不同平台对优先级的定义不同，skill-router 提供灵活配置:

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `tier_order` | `["project", "user"]` | 层级优先级 (项目级优先于用户级) |
| `platform_weight` | `1.0` (全部均等) | 各平台匹配得分权重 |
| `override_same_name` | `project > user` | 同名 skill 覆盖规则 |

默认逻辑: **项目级 > 用户级** (无论来源平台)，同层级内**所有平台均等**。

#### 路径解析规则

- 项目级路径: 相对于 `--cwd` 参数或当前工作目录
- 用户级路径: 相对于 `$HOME`
- 路径存在性: 只扫描实际存在的目录 (不产生 I/O 错误)
- Claude Code 嵌套扫描: 如果检测到 `.claude/skills/`，也递归扫描子目录

### 2.2 三层意图识别

```
user prompt
    │
    ▼
┌─────────────────────────────────────────────┐
│  l1: keyword / exact match                  │
│  ├ 检查 SKILL.md frontmatter 的 triggers     │
│  ├ 检查 skill name 是否包含子串               │
│  └ 命中 → 直接返回 (conf ≈ 1.0)              │
├─────────────────────────────────────────────┤
│  l2: tf-idf semantic match                  │
│  ├ 对 user prompt 做分词/ngram               │
│  ├ 对 skill description + triggers + keywords │
│  ├ 计算 cosine similarity                    │
│  ├ 来源权重: project * 1.2, global * 1.0     │
│  └ 排名 → 返回 top-k with scores              │
├─────────────────────────────────────────────┤
│  l3: llm secondary judgment (可选)          │
│  ├ 当 top-1 conf < 阈值 或 top-1 ≈ top-2     │
│  ├ LLM 做意图消歧                             │
│  │  ├ 判断是否属于同一任务的多 skill 协作     │
│  │  ├ 或判断是否是互斥方案                     │
│  │  └ 或直接向用户提问: "你要 A 还是 B?"      │
│  └ 返回结果 (含 multi-skill 建议)              │
└─────────────────────────────────────────────┘
```

### 2.3 意图消歧与多 skill 检测

L3 LLM 判断的一个重要功能是检测一个 prompt 是否需要**多个 skill 协作**。

#### 典型场景

| 场景 | 例子 | 检测到的 skill | 关系 |
|------|------|---------------|------|
| **流水线** | "帮我写一篇论文综述" | paper-reading(读懂原文) → thesis-writing(写综述) | 顺序依赖 |
| **并行** | "查一下今天的 Git 趋势和 AI 新闻" | github-trending + web-research | 独立并行 |
| **互补** | "检查一下我的 React 代码" | code-review + linting | 叠加互补 |
| **替代** | "写一个 git commit" | ai-git-best-practices vs commit-skill | 互斥二选一 |

#### 决策逻辑

```
L2 输出 top-3 candidates
    │
    ├── 如果 top-1 > top-2 by ≥0.3
    │   └── → 单一 skill, 直接路由 (同 2.2 节)
    │
    ├── 如果 top-1 ≈ top-2 (差距 <0.3)
    │   │
    │   ├── L3 llm 判断关系
    │   │   ├── 流水线关系 → multi_plan {skills: [A, B], mode: "pipeline"}
    │   │   ├── 并行关系   → multi_plan {skills: [A, B], mode: "parallel"}
    │   │   ├── 互补关系   → multi_plan {skills: [A, B], mode: "compose"}
    │   │   └── 替代关系   → 向用户确认: "你要 A 还是 B?"
    │   │
    │   └── 如果 llm 不可用 → 向用户展示 top-3, 让用户选
    │
    └── 如果所有分数 < low_confidence
        └── → 网络搜索回退
```

#### 组合模式 (Mode) 说明

| Mode | 含义 | 输出结构 |
|------|------|---------|
| `single` | 单个 skill | `{action: "invoke", skill: X}` |
| `pipeline` | 顺序执行, 前一个的输出是后一个的输入 | `{action: "orchestrate", mode: "pipeline", skills: [A → B → C]}` |
| `parallel` | 独立并行, 结果合并 | `{action: "orchestrate", mode: "parallel", skills: [A, B]}` |
| `compose` | 同时加载, 互相补充 | `{action: "orchestrate", mode: "compose", skills: [A, B]}` |
| `choose` | 互斥方案, 用户二选一 | `{action: "choose", candidates: [A, B]}` |

#### 重要边界

- **skill-router 不执行 skill** — 它只返回 orchestration plan, 由调用方决定怎么执行
- **组合关系是启发式的** — 基于 L3 LLM 分析, 不是写死的兼容矩阵
- **调用方可以忽略组合建议** — CLI 展示给用户选择, API 返回 plan 让 agent 决定
| `medium_confidence` | 0.50 | L2得分≥此值 → 建议用户确认 |
| `low_confidence` | 0.20 | L2得分≥此值 → 走L3 LLM判断 |
| `fallback` | <0.20 | 无本地匹配 → 走网络搜索 |

### 2.3 网络搜索回退

当本地 (project + global) 无匹配时:

```
user prompt
    │
    ▼
┌─────────────────────────────────────────────┐
│  network search                             │
│  ├ npx skills find "<prompt>"               │
│  ├ 解析返回结果列表                          │
│  └ 返回 top-3                               │
├─────────────────────────────────────────────┤
│  install proposal                           │
│  ├ 展示搜索结果给用户                        │
│  ├ "找到 skill-X, 是否安装?"                 │
│  └ 用户确认 → npx skills add ...            │
└─────────────────────────────────────────────┘
```

---

## 3. 核心数据类型

```python
from enum import Enum

class Platform(str, Enum):
    """已知的 agent 平台."""
    CLAUDE = "claude"
    WORKBUDDY = "workbuddy"
    OPENCODE = "opencode"
    OPENCLAW = "openclaw"
    GEMINI = "gemini"
    CODEX = "codex"
    CURSOR = "cursor"
    AGENTS = "agents"        # Universal ~/.agents/skills/
    UNKNOWN = "unknown"      # 用户自定义路径

class Tier(str, Enum):
    """skill 所属层级."""
    PROJECT = "project"
    USER = "user"
    NETWORK = "network"

@dataclass
class SkillMeta:
    """从 SKILL.md 解析的元数据."""
    name: str
    description: str
    triggers: list[str]      # frontmatter triggers 字段
    tier: Tier               # "project" | "user"
    platform: Platform       # 来源平台
    source_path: str         # SKILL.md 完整路径

class Mode(str, Enum):
    """路由模式: 单 skill 或多 skill 编排."""
    SINGLE = "single"
    PIPELINE = "pipeline"
    PARALLEL = "parallel"
    COMPOSE = "compose"
    CHOOSE = "choose"

@dataclass
class RouteResult:
    """路由结果."""
    mode: Mode               # 路由模式
    skill: SkillMeta | None  # 主要匹配 (single 模式时)
    skills: list[SkillMeta]  # 多 skill 列表 (pipeline/parallel/compose 模式时)
    candidates: list[tuple[SkillMeta, float]]  # top-k 完整候选列表
    score: float             # 最高分 (0.0 ~ 1.0)
    confidence: str          # "high" | "medium" | "low" | "fallback"
    action: str              # "invoke" | "orchestrate" | "choose" | "confirm" | "network_search"

@dataclass
class NetworkSkill:
    """从社区搜索到的 skill."""
    name: str
    description: str
    install_cmd: str         # e.g. "npx skills add owner/repo@name"
    source_url: str          # e.g. "https://skills.sh/owner/repo/name"
```

---

## 4. 模块分解

```
skill-router/
├── pyproject.toml           # 项目配置, CLI 入口定义
├── skill-router.toml        # 默认配置文件 (用户可覆盖为 ~/.config/skill-router.toml)
├── README.md
├── src/
│   └── skill_router/
│       ├── __init__.py
│       ├── types.py         # SkillMeta, RouteResult, Platform, Tier 枚举
│       ├── config.py        # 配置加载 (TOML, 平台路径注册表, 自定义路径)
│       ├── scanner/
│       │   ├── __init__.py
│       │   ├── registry.py  # 平台注册表: 内置 8 个平台 + 用户自定义
│       │   ├── scanner.py   # 统一扫描编排: 遍历平台 → 扫描路径
│       │   ├── parser.py    # SKILL.md frontmatter 解析
│       │   └── platforms.py # 每个平台的路径定义 + 检测逻辑
│       ├── matcher/
│       │   ├── __init__.py
│       │   ├── keyword.py   # L1 关键词/精确匹配
│       │   ├── tfidf.py     # L2 TF-IDF 语义匹配
│       │   └── llm.py       # L3 LLM 二次判断 (含多skill关系分析)
│       ├── composer/
│       │   ├── __init__.py
│       │   ├── relations.py # skill 关系分析 (pipeline/parallel/compose/choose)
│       │   └── plan.py      # 编排计划生成
│       ├── network/
│       │   ├── __init__.py
│       │   ├── search.py    # skills.sh / GitHub 搜索
│       │   └── installer.py # 用户确认后执行安装
│       ├── router.py        # 主路由编排: 扫描 → 匹配 → 决策 → 编排
│       └── cli.py           # Typer CLI 入口
├── tests/
│   ├── test_types.py
│   ├── test_scanner/
│   │   ├── test_registry.py
│   │   ├── test_parser.py
│   │   └── test_platforms.py
│   ├── test_matcher/
│   ├── test_composer/
│   │   ├── test_relations.py
│   │   └── test_plan.py
│   ├── test_network/
│   └── test_router.py
└── docs/
    └── ARCHITECTURE.md
```

### 依赖策略

| 依赖 | 用途 | 强制/可选 |
|------|------|-----------|
| `typer>=0.25` | CLI | 强制 |
| `rich>=15.0` | 输出美化 | 强制 |
| `numpy>=2.0` | TF-IDF 向量运算 | 强制 |
| `httpx>=0.28` | HTTP 请求 | 强制 |
| `anthropic>=0.50` | L3 LLM 判断 | 可选 `[llm]` |

**关键决策**: TF-IDF 用 `numpy` 手写，不依赖 `scikit-learn`。原因:
- scikit-learn 是 70MB+ 的包，80% 的功能用不到
- TF-IDF 的核心是 `CountVectorizer` + `TfidfTransformer`，numpy 手写约 100 行
- 保持极简, 和 agent-skill-infra 的设计哲学一致

---

## 5. CLI 设计

```bash
# 查询: 单次路由
skill-route "帮我写一篇论文综述"              # 默认上下文 (自动检测平台)
skill-route "帮我写一篇论文综述" --cwd ./     # 指定项目目录
skill-route "帮我写一篇论文综述" --json       # JSON 输出

# 单 skill 结果示例:
# ✓ 匹配: paper-reading (user · claude · confidence: 0.87)
#   @ ~/.claude/skills/paper-reading/SKILL.md (via claude)

# 多 skill 结果示例:
# skill-route "帮我写一篇论文综述"
# → 检测到多 skill 协作:
#   ① paper-reading (0.87)    — 文献阅读与理解
#   ② thesis-writing (0.72)   — 论文写作
#   ③ citation-check (0.45)   — 引文验证
#   关系: 流水线 (paper-reading → thesis-writing → citation-check)
#   操作: [u] 用全部  [p] 挑选  [c] 取消

# 并行多 skill
# skill-route "查一下今天的 GitHub 趋势和 AI 新闻"
# → 检测到并行 skill:
#   ① github-trending (0.91)
#   ② web-research (0.85)
#   关系: 独立并行 (可同时执行)
#   操作: [u] 同时执行  [p] 挑选  [c] 取消

# 互斥选择
# skill-route "写一个 git commit"
# → 检测到替代方案:
#   ① ai-git-best-practices (0.82)  — 按规范写 commit
#   ② commit-skill (0.78)           — 自动生成 commit
#   关系: 互斥 (二选一)
#   请选择: [1] ai-git-best-practices  [2] commit-skill  [c] 取消

# 平台管理
skill-route platforms                       # 列出检测到的平台
skill-route platforms scan                  # 重新扫描检测平台
skill-route platforms add my-agent ~/.my-agent/skills  # 注册自定义平台

# 索引管理
skill-route index rebuild                   # 重建 skill 索引
skill-route index list                      # 列出所有已索引 skill
skill-route index stats                     # 索引统计 (按平台分组)

# 网络搜索 (跳过本地匹配)
skill-route search "react component generator"

# 网络搜索 (跳过本地匹配)
skill-route search "react component generator"

# 交互式
skill-route                                 # 交互式终端
```

### --json 输出 (给脚本/CI 解析用)

所有命令支持 `--json` 输出结构化数据:

```json
// 单 skill
$ skill-route "帮我写论文综述" --json
→
{
  "mode": "single",
  "skill": {
    "name": "paper-reading",
    "description": "Read and summarize academic papers",
    "platform": "claude",
    "tier": "user",
    "source_path": "/Users/me/.claude/skills/paper-reading/SKILL.md"
  },
  "score": 0.87,
  "confidence": "high",
  "action": "invoke"
}

// 多 skill 流水线
$ skill-route "帮我写论文综述" --json
→
{
  "mode": "pipeline",
  "skills": [
    {"name": "paper-reading", "platform": "claude", "tier": "user"},
    {"name": "thesis-writing", "platform": "workbuddy", "tier": "project"}
  ],
  "candidates": [["paper-reading", 0.87], ["thesis-writing", 0.72], ["citation-check", 0.45]],
  "score": 0.87,
  "confidence": "high",
  "action": "orchestrate"
}

// 互斥选择
$ skill-route "写一个 git commit" --json
→
{
  "mode": "choose",
  "candidates": [
    {"name": "ai-git-best-practices", "description": "...", "score": 0.82},
    {"name": "commit-skill", "description": "...", "score": 0.78}
  ],
  "action": "choose"
}
POST /route
{"prompt": "查一下 GitHub 趋势和 AI 新闻", "cwd": "/path/to/project"}
→
{
  "mode": "parallel",
  "skills": [
    {"name": "github-trending", "...", "confidence": 0.91},
    {"name": "web-research", "...", "confidence": 0.85}
  ],
  "action": "orchestrate",
  "orchestration": {
    "mode": "parallel",
    "steps": [
      {"skill": "github-trending", "task": "fetch_trending"},
      {"skill": "web-research", "task": "search_news"}
    ]
  }
}

// 互斥选择
POST /route
{"prompt": "写一个 git commit"}
→
{
  "mode": "choose",
  "candidates": [
    {"name": "ai-git-best-practices", "confidence": 0.82},
    {"name": "commit-skill", "confidence": 0.78}
  ],
  "action": "choose"
}

---

## 6. 实现阶段

### Phase 0: 项目脚手架 (估计 1 天)
- 初始化 pyproject.toml (Python 3.12, uv workspace)
- 建立模块目录结构
- `types.py` 定义核心数据类型 (包括 Platform/Tier 枚举)
- `config.py` 骨架 + 默认配置 TOML
- `cli.py` 骨架 (skill-route --help)
- 测试框架: pytest + ruff + pyright

### Phase 1: 跨平台扫描器 + 解析器 (估计 3 天)
- `scanner/parser.py`: SKILL.md frontmatter 解析 (复用 agent-skill-infra 的 _parse_front_matter)
- `scanner/registry.py`: 平台注册表
  - 内置 8 个平台 (Claude, WorkBuddy, OpenCode, OpenClaw, Gemini, Codex, Cursor, Universal)
  - 每个平台定义 user-level 和 project-level 路径
  - 支持用户 `register_platform()` 添加自定义平台
- `scanner/platforms.py`: 平台检测逻辑
  - `detect_platforms(cwd)` → 返回当前环境中激活的平台列表
  - 检测方法: 检查路径是否存在, 是否有 SKILL.md 子目录
  - 自动发现 Claude Code 的嵌套 `.claude/skills/` 子目录
- `scanner/scanner.py`: 统一扫描编排
  - 遍历所有激活平台的 user-level + project-level 路径
  - 递归扫描每个路径下的 `*/SKILL.md`
  - 返回 `list[SkillMeta]`
  - 去重: 同名 skill 按优先级规则 (可配置)
- 测试: 模拟多平台 skill 目录结构, 验证扫描 + 解析

### Phase 2: 匹配器 (估计 3 天)
- `matcher/keyword.py`: 精确关键词匹配 (triggers + name substring)
- `matcher/tfidf.py`: numpy 手写 TF-IDF
  - bigram 分词 (支持中英文混合)
  - cosine similarity
  - 来源权重: project * 1.2, global * 1.0
- 阈值决策逻辑
- 测试: 构建测试 skill 集, 验证匹配准确性

### Phase 3: 主路由 + CLI (估计 2 天)
- `router.py`: 三层匹配编排
  - L1 keyword → L2 TF-IDF → 阈值决策 → L3 LLM 或网络回退
  - 结果包装成 RouteResult
- `cli.py` 完整命令: route, index rebuild, index list, index stats, search, serve
- 输出格式化: Rich table / JSON
- 测试: 集成测试 (扫描 → 匹配 → 路由)

### Phase 4: 网络回退 (估计 2 天)
- `network/search.py`: 调用 `npx skills find` 并解析结果
- `network/installer.py`: 用户确认后执行 `npx skills add`
- 网络超时和离线回退
- 单元测试 (mock npx 调用)

### Phase 5: L3 LLM + 配置系统 (估计 2 天)
- `matcher/llm.py`: Anthropic Claude 做意图消歧 (含多skill关系分析)
- `composer/`: skill 关系检测 + 编排计划生成
- 配置系统: TOML 配置文件 `~/.config/skill-router.toml`
  - 平台路径自定义
  - 阈值调整
  - LLM API key 配置
- 自学习机制: 用户纠正路由后, 提取关键词重建索引

---

## 7. 与 agent-skill-infra 的集成路径

```toml
# agent-skill-infra/pyproject.toml 新增
[project.optional-dependencies]
router = ["skill-router>=0.1.0"]
llm = ["httpx>=0.28.1"]
```

用户安装: `pip install agent-skill-infra[router]` 自动拉 skill-router.

集成点:
- agent-skill-infra 的 `skill-quality` 可用 skill-router 的路由结果来优化测试选择
- agent-skill-infra 的 `skill-test` 可用 skill-router 定位的 skill 自动运行对应测试
- 但 skill-router 本身不依赖 agent-skill-infra，也不依赖任何特定平台

**skill-router 是平台无关的底层设施**，agent-skill-infra 只是它的一个可选消费者。

---

## 8. 设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 是否依赖 agent-skill-infra | 否 | 复用~70行代码 vs 交叉依赖长期成本 |
| 平台范围 | 8个内置平台 + 用户自定义 | 不能只支持 WorkBuddy, 要通用 |
| 平台检测方式 | 路径存在性检查 + 可配置注册表 | 自动发现, 零配置上手 |
| 优先级规则 | project > user, 平台均等 | 灵活可配置 |
| TF-IDF 实现方式 | numpy 手写 | 避免 scikit-learn 70MB 包袱 |
| 网络搜索回退 | 需用户确认 | 不适合自动安装未审计 skill |
| CLI 交互 | 交互式终端 + `--json` | CLI 给人用, JSON 给脚本/CI 用 |
| LLM 判断 | 可选 `[llm]` | 保持核心零 LLM 依赖 |
| 配置系统 | TOML 文件 | 简单, 用户可覆盖默认配置 |

---

## 9. 未纳入本次设计 (v0.1 不包含)

- HTTP API / serve 模式 (v0.1 只做 CLI)
- FAISS/向量数据库支持 (超出 1000 skill 时考虑)
- bge-m3 嵌入 (不如 TF-IDF 零依赖可靠)
- ReAct 多步任务编排 (这是 GSD 的领域)
- Web UI (先 CLI + API 验证 PMF)
- skill 执行引擎 (只路由, 不执行 — 编排计划由调用方执行)
- 自动化测试 (v0.1 不包含 composer 模块的自动化测试, 先验证概念)
