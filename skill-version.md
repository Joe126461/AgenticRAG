# Agent Template vNext

> 目标：把这个文件当作一个长期可维护的 agent 模版，而不是一次性的 prompt。
> 核心原则：稳定内核、注册式扩展、渐进式披露、工具和 MCP 优先发现。
> 设计取向：参考当前主流 agent 体系的组织方式，尤其是 `YAML 头 + Markdown 正文` 的 skill 设计，以及 OpenClaw 一类偏“声明式 skill + 运行时发现”的思路。

---

## 1. 这份模版解决什么问题

这份模版的目标不是“写一个很长的系统提示词”，而是提供一套工业级的 agent 组织方式：

- 内核稳定：核心行为、执行循环、安全边界尽量不改。
- 扩展简单：新增 skill、MCP server、工具，不需要重写主体。
- 渐进加载：运行时只读取当前任务真正需要的 skill 内容，避免上下文膨胀。
- MCP 优先：优先发现已有 server / resource / template / prompt，而不是手搓逻辑。
- 结构清晰：便于多人协作、版本升级、跨运行时迁移。

---

## 2. 设计总览

推荐把 agent 划分为 5 层：

1. `Core Contract`
   说明 agent 的共同行为，不随业务频繁变化。
2. `Tool Presets`
   说明默认有哪些工具能力、优先级、fallback 和安全边界。
3. `Skill Registry`
   只负责声明有哪些 skill、何时触发、入口文件在哪里。
4. `MCP Registry`
   只负责声明有哪些 MCP server、如何发现、何时优先使用。
5. `Skill Files`
   每个 skill 独立成一个 `YAML front matter + Markdown body` 文件，正文按需阅读。

这意味着：

- 新增能力，优先是“加文件 + 加 registry 条目”
- 而不是“改系统提示词主干”

---

## 3. 推荐文件结构

这是一个适合长期维护的目录结构：

```text
agent-template/
├─ AGENT.md
├─ registries/
│  ├─ tools.yaml
│  ├─ skills.yaml
│  ├─ mcp-servers.yaml
│  └─ profiles.yaml
├─ skills/
│  ├─ workspace-inspector/
│  │  ├─ SKILL.md
│  │  └─ examples.md
│  ├─ patch-editor/
│  │  ├─ SKILL.md
│  │  └─ examples.md
│  ├─ test-runner/
│  │  ├─ SKILL.md
│  │  └─ examples.md
│  ├─ mcp-context-loader/
│  │  ├─ SKILL.md
│  │  └─ examples.md
│  └─ api-implementer/
│     ├─ SKILL.md
│     └─ examples.md
├─ mcp/
│  ├─ filesystem/
│  │  └─ server.json
│  ├─ git/
│  │  └─ server.json
│  ├─ docs/
│  │  └─ server.json
│  └─ browser/
│     └─ server.json
├─ prompts/
│  ├─ core-system.md
│  ├─ core-execution.md
│  └─ response-style.md
└─ examples/
   ├─ add-skill.md
   ├─ add-mcp.md
   └─ add-tool.md
```

如果你想最小化：

- `AGENT.md`
- `registries/*.yaml`
- `skills/*/SKILL.md`

这 3 类文件已经足够支撑一套可扩展 agent。

---

## 4. Core Contract

这一段是框架层，应该尽量少改。

### 4.1 Agent 角色

这个 agent 是一个具备工程执行能力的协作体，它应该：

- 在改动前先读上下文
- 优先复用已有 skill、工具、MCP server
- 能做就做，少停在“建议”阶段
- 在 sandbox 内安全执行
- 只在必要时请求升级权限
- 不覆盖用户的无关改动
- 对结果做最轻量但可靠的验证

### 4.2 不可破坏规则

- 不读文件就不要假设文件内容
- 不随意重写核心 prompt 主体
- 不回滚无关改动
- 不默认执行破坏性命令
- 不把一次性的业务规则写进框架内核
- 新能力优先通过注册和挂载加入

### 4.3 执行循环

每次任务都按这个循环来：

1. 识别任务类型
2. 列目录、搜文件、读关键文件
3. 检查是否有匹配 skill
4. 检查是否有匹配 MCP server / resource / template / prompt
5. 选择最小够用的工具集
6. 实施修改
7. 运行验证
8. 输出修改说明、验证结果、剩余风险

---

## 5. Tool Presets

下面这些是建议内置的基础工具层。新增工具时，不要直接写散文式说明，应该追加到 registry。

### 5.1 推荐内置工具清单

```yaml
version: 1
tool_presets:
  shell:
    enabled: true
    preferred_shell: bash
    fallback_shells: [sh, powershell]
    use_cases:
      - read_files
      - list_files
      - search_code
      - run_tests
      - run_build
      - inspect_env
    preferred_commands:
      find_files: "rg --files"
      search_text: "rg"
      list_dir: "ls -la"
      read_chunk: "sed -n '1,200p'"
      git_status: "git status --short"
    fallback_commands:
      find_files: "find . -type f"
      list_dir_windows: "Get-ChildItem -Force"
      search_text_windows: "Select-String"
    safety:
      deny_by_default:
        - destructive_fs
        - privilege_escalation

  sandbox:
    enabled: true
    mode: workspace-write
    escalation_required_for:
      - network_install
      - out_of_workspace_write
      - gui_launch
      - destructive_actions
      - system_service_control
    strategy:
      - inspect_locally_first
      - request_approval_only_when_blocked

  listing:
    enabled: true
    purpose:
      - enumerate_workspace
      - locate_extension_points
      - reduce_edit_scope

  patch_editing:
    enabled: true
    preferred_method: patch
    constraints:
      - preserve_unrelated_content
      - small_auditable_diffs
      - ascii_by_default

  mcp_discovery:
    enabled: true
    purpose:
      - list_servers
      - inspect_resources
      - inspect_resource_templates
      - inspect_prompts_if_supported
      - prefer_structured_context_over_guessing

  skill_discovery:
    enabled: true
    purpose:
      - discover_installed_skills
      - read_only_needed_skill_file
      - apply_progressive_disclosure
```

---

## 6. Skill 设计

这一节是这次改造的重点。

现代 skill 文件更推荐使用：

- `YAML front matter` 承载声明式元数据
- `Markdown body` 承载执行说明
- 正文按“渐进式披露”组织，而不是一上来塞满全部细节

这和当前很多 agent 体系、包括 OpenClaw 风格中强调的“声明式发现 + 运行时按需读取”是相容的。

### 6.1 为什么要用 YAML 头 + Markdown

好处很直接：

- 机器更容易做 skill discovery 和 routing
- 人更容易读和维护
- 元数据和正文职责分离
- 可以只读取 front matter 做路由，再决定是否继续读取正文
- 可以把 examples、references、checklist 拆到子文件，天然支持渐进式披露

### 6.2 Skill 文件标准结构

每个 skill 推荐至少有一个 `SKILL.md`：

```md
---
id: skill.workspace-inspector
name: Workspace Inspector
version: 1.0.0
category: coding
summary: >
  快速理解代码库结构、关键入口和潜在改动点，作为大多数编码任务的前置 skill。
tags:
  - discovery
  - codebase
  - routing
triggers:
  explicit_mentions:
    - "@workspace-inspector"
  task_patterns:
    - "读代码库"
    - "理解项目结构"
    - "定位改动入口"
inputs:
  required: []
  optional:
    - focus_paths
    - target_feature
tools:
  required:
    - shell
    - listing
  optional:
    - mcp_discovery
mcp:
  preferred_servers:
    - filesystem
    - docs
routing:
  priority: 100
  when_to_use: >
    当任务需要先理解项目结构、找到入口文件、识别扩展点时优先使用。
  when_not_to_use: >
    当任务已经给出明确文件和明确改动点时，不必强制走完整探索流程。
safety:
  requires_escalation: false
  destructive_risk: low
outputs:
  produces:
    - target_files
    - architecture_summary
    - edit_plan
disclosure:
  strategy: progressive
  read_order:
    - summary
    - workflow
    - decision_rules
    - examples
---

# Workspace Inspector

## Purpose

用于在最短路径内理解一个代码库，输出可执行的修改入口，而不是做漫无目的的全仓阅读。

## Workflow

1. 先列目录，确认顶层结构。
2. 搜索入口文件、配置文件、框架特征。
3. 读取最相关的少量文件，不做全量展开。
4. 标出最可能的改动点和验证点。

## Decision Rules

- 如果任务范围很大，先缩小到子目录。
- 如果已有 MCP 资源能提供结构化上下文，优先读 MCP。
- 如果用户点名了文件，先围绕目标文件建立局部上下文。

## Output Contract

输出至少包含：

- 关键文件列表
- 推荐改动入口
- 需要联动验证的位置

## Examples

更多例子见 `examples.md`
```

### 6.3 渐进式披露怎么做

推荐按这几个层级组织 skill：

1. `front matter`
   只放路由、能力、输入、工具、风险、输出声明
2. `Purpose`
   简短说明 skill 是做什么的
3. `Workflow`
   只保留核心步骤
4. `Decision Rules`
   什么时候用、什么时候不要用
5. `Output Contract`
   定义输出最小标准
6. `Examples / References`
   放到额外文件，不默认加载

这样做的结果是：

- 路由时只读 YAML 头
- 命中后先读摘要和 workflow
- 只有在复杂任务里才继续读 examples / references

这就是最实用的渐进式披露。

---

## 7. MCP 设计

你提到“也检查 MCP，并与时俱进”，这里要把 MCP 从“工具列表”升级成“能力发现层”。

现代 MCP 相关设计，建议至少考虑这些能力维度：

- `tools`
- `resources`
- `resource templates`
- `prompts`

不是每个 server 都必须全支持，但 registry 应该声明清楚。

### 7.1 MCP Server 条目标准结构

```yaml
id: mcp.filesystem
name: Filesystem Server
version: 1.0.0
transport: stdio
purpose: >
  提供工作区文件系统相关的结构化上下文、资源读取和辅助工具。
capabilities:
  tools: true
  resources: true
  resource_templates: true
  prompts: false
discovery:
  strategy:
    - list_resources_first
    - inspect_templates_if_query_is_parametric
    - use_tools_for_actions_only
use_when:
  - 需要结构化文件上下文
  - 需要将文件系统作为 MCP 资源暴露
avoid_when:
  - 本地 shell 已足够且任务非常简单
trust:
  level: high
fallback:
  - use_shell_listing
  - read_local_files_directly
```

### 7.2 MCP 使用原则

- 发现优先于硬编码
- resource 优先于纯文本猜测
- template 优先于重复拼接参数
- tool 用于执行动作，不要把所有上下文都塞进 tool 调用
- 一个任务可以先用 resource 建上下文，再用 tool 执行动作

---

## 8. 一套真实可用的初始 Skill Registry

下面是一份适合 coding agent 的初始配置。它不是玩具例子，而是可以直接作为第一版挂载。

```yaml
version: 1
skills:
  - id: skill.workspace-inspector
    name: Workspace Inspector
    path: ./skills/workspace-inspector/SKILL.md
    category: coding
    summary: "理解项目结构、关键入口与改动点。"
    triggers:
      explicit_mentions: ["@workspace-inspector"]
      task_patterns:
        - "理解代码库"
        - "定位文件"
        - "找入口"
    tools_required: [shell, listing]
    mcp_preferred: [filesystem, docs]
    priority: 100

  - id: skill.patch-editor
    name: Patch Editor
    path: ./skills/patch-editor/SKILL.md
    category: coding
    summary: "用小而可审计的 diff 修改文件。"
    triggers:
      explicit_mentions: ["@patch-editor"]
      task_patterns:
        - "修改代码"
        - "重构小范围逻辑"
        - "修补配置"
    tools_required: [patch_editing]
    mcp_preferred: []
    priority: 120

  - id: skill.test-runner
    name: Test Runner
    path: ./skills/test-runner/SKILL.md
    category: coding
    summary: "识别合适的测试入口并运行最小可靠验证。"
    triggers:
      explicit_mentions: ["@test-runner"]
      task_patterns:
        - "运行测试"
        - "验证改动"
        - "检查回归"
    tools_required: [shell]
    mcp_preferred: []
    priority: 90

  - id: skill.mcp-context-loader
    name: MCP Context Loader
    path: ./skills/mcp-context-loader/SKILL.md
    category: ops
    summary: "发现并读取与任务相关的 MCP 资源、模板和 prompt。"
    triggers:
      explicit_mentions: ["@mcp", "@mcp-context-loader"]
      task_patterns:
        - "读取 MCP 上下文"
        - "发现 MCP server"
        - "资源驱动任务"
    tools_required: [mcp_discovery]
    mcp_preferred: [filesystem, docs, api-spec]
    priority: 130

  - id: skill.api-implementer
    name: API Implementer
    path: ./skills/api-implementer/SKILL.md
    category: coding
    summary: "围绕接口、handler、schema、service 做增量实现。"
    triggers:
      explicit_mentions: ["@api-implementer"]
      task_patterns:
        - "新增接口"
        - "修改 API"
        - "补 schema"
    tools_required: [shell, listing, patch_editing]
    mcp_preferred: [docs, api-spec]
    priority: 110

  - id: skill.frontend-editor
    name: Frontend Editor
    path: ./skills/frontend-editor/SKILL.md
    category: frontend
    summary: "在既有设计语言内改 UI、交互和样式。"
    triggers:
      explicit_mentions: ["@frontend-editor"]
      task_patterns:
        - "改页面"
        - "改组件"
        - "修样式"
    tools_required: [shell, listing, patch_editing]
    mcp_preferred: [browser, docs]
    priority: 100

  - id: skill.docs-writer
    name: Docs Writer
    path: ./skills/docs-writer/SKILL.md
    category: docs
    summary: "生成 README、迁移说明、使用文档和变更说明。"
    triggers:
      explicit_mentions: ["@docs-writer"]
      task_patterns:
        - "写文档"
        - "补 README"
        - "补迁移说明"
    tools_required: [shell, patch_editing]
    mcp_preferred: [docs]
    priority: 70
```

---

## 9. 一套真实可用的初始 MCP Registry

下面是一个偏通用、适合工程 agent 的第一版 MCP 配置。

```yaml
version: 1
mcp_servers:
  - id: filesystem
    name: Filesystem Server
    config_path: ./mcp/filesystem/server.json
    transport: stdio
    purpose: "暴露工作区文件、目录和结构化资源。"
    capabilities:
      tools: true
      resources: true
      resource_templates: true
      prompts: false
    discovery:
      read_priority:
        - resources
        - resource_templates
        - tools
    use_when:
      - "需要结构化工作区上下文"
      - "需要基于资源而不是裸文本读文件"
    fallback:
      - "shell listing"
      - "direct file reads"
    trust_level: high

  - id: git
    name: Git Server
    config_path: ./mcp/git/server.json
    transport: stdio
    purpose: "暴露分支、变更、提交、diff 等版本控制上下文。"
    capabilities:
      tools: true
      resources: true
      resource_templates: false
      prompts: false
    discovery:
      read_priority:
        - resources
        - tools
    use_when:
      - "需要结构化 git 变更信息"
      - "需要避免手工解析复杂 diff"
    fallback:
      - "git status"
      - "git diff"
    trust_level: high

  - id: docs
    name: Docs Server
    config_path: ./mcp/docs/server.json
    transport: stdio
    purpose: "暴露项目内部文档、设计说明、规范和决策记录。"
    capabilities:
      tools: true
      resources: true
      resource_templates: true
      prompts: true
    discovery:
      read_priority:
        - resources
        - prompts
        - resource_templates
    use_when:
      - "任务依赖规范、设计文档或历史决策"
    fallback:
      - "search markdown files locally"
    trust_level: high

  - id: api-spec
    name: API Spec Server
    config_path: ./mcp/api-spec/server.json
    transport: stdio
    purpose: "暴露 OpenAPI、JSON Schema、接口约束和参数模板。"
    capabilities:
      tools: true
      resources: true
      resource_templates: true
      prompts: false
    discovery:
      read_priority:
        - resources
        - resource_templates
        - tools
    use_when:
      - "任务是实现或修改 API"
      - "需要读取 schema 约束"
    fallback:
      - "read local openapi files"
    trust_level: high

  - id: browser
    name: Browser Server
    config_path: ./mcp/browser/server.json
    transport: stdio
    purpose: "提供本地页面打开、交互检查和截图能力。"
    capabilities:
      tools: true
      resources: false
      resource_templates: false
      prompts: false
    discovery:
      read_priority:
        - tools
    use_when:
      - "需要查看 localhost 页面"
      - "需要验证前端交互或视觉结果"
    fallback:
      - "manual reasoning if browser unavailable"
    trust_level: medium
```

---

## 10. 如何加一个 Tool

新增工具时，建议做 3 步：

### 10.1 在 `registries/tools.yaml` 里加预设

```yaml
playwright:
  enabled: true
  category: browser
  purpose:
    - inspect_local_ui
    - automate_browser_checks
  safety:
    escalation_required: false
  preferred_when:
    - "需要验证页面实际行为"
```

### 10.2 在相关 skill 的 front matter 里引用它

```yaml
tools:
  required:
    - shell
    - playwright
```

### 10.3 在执行规则里声明优先级

比如：

- 本地浏览器验证优先于纯静态猜测
- 但只有在前端任务时才拉起

核心点：

- tool preset 定义“这类工具是什么”
- skill 定义“什么时候用它”

不要把这两层混在一起。

---

## 11. 如何加一个 MCP Server

新增 MCP server 推荐做 4 步：

### 11.1 新建目录

```text
mcp/
└─ your-server/
   └─ server.json
```

### 11.2 在 `server.json` 里定义连接方式

示例：

```json
{
  "name": "your-server",
  "transport": "stdio",
  "command": "node",
  "args": ["./dist/index.js"]
}
```

### 11.3 在 `registries/mcp-servers.yaml` 里注册

```yaml
- id: your-server
  name: Your Server
  config_path: ./mcp/your-server/server.json
  transport: stdio
  purpose: "提供某类结构化上下文或执行能力"
  capabilities:
    tools: true
    resources: true
    resource_templates: false
    prompts: false
  use_when:
    - "某类任务"
```

### 11.4 在相关 skill 里声明 preferred server

```yaml
mcp:
  preferred_servers:
    - your-server
```

推荐原则：

- 有结构化上下文就走 resource / template
- 有执行动作才走 tool
- 不要把所有事情都塞进一个万能 MCP

---

## 12. 如何加一个 Skill

新增 skill 最推荐的路径是：

### 12.1 新建目录

```text
skills/
└─ my-skill/
   ├─ SKILL.md
   └─ examples.md
```

### 12.2 写 `SKILL.md`

先写 YAML 头，再写 Markdown 正文。

最小可用版本：

```md
---
id: skill.my-skill
name: My Skill
version: 1.0.0
category: coding
summary: >
  这里写一句话说明这个 skill 的用途。
triggers:
  explicit_mentions:
    - "@my-skill"
  task_patterns:
    - "这类任务"
tools:
  required:
    - shell
routing:
  priority: 90
safety:
  requires_escalation: false
outputs:
  produces:
    - result_summary
disclosure:
  strategy: progressive
  read_order:
    - summary
    - workflow
    - examples
---

# My Skill

## Purpose

一句话说清它是干什么的。

## Workflow

1. inspect
2. execute
3. validate

## Output Contract

- 给出结果
- 给出验证
```

### 12.3 在 `registries/skills.yaml` 里注册

```yaml
- id: skill.my-skill
  name: My Skill
  path: ./skills/my-skill/SKILL.md
  category: coding
  summary: "一句话摘要"
  triggers:
    explicit_mentions: ["@my-skill"]
    task_patterns: ["这类任务"]
  tools_required: [shell]
  mcp_preferred: []
  priority: 90
```

### 12.4 保持“窄 skill”

一个 skill 最好只解决一类清晰问题，不要做成超级万能 skill。

推荐拆法：

- `workspace-inspector`
- `patch-editor`
- `test-runner`
- `api-implementer`
- `frontend-editor`
- `docs-writer`

而不是一个 `universal-coding-skill`。

---

## 13. 一份可直接复用的 AGENT 主体骨架

你可以把这段作为 `AGENT.md` 主体：

```md
# Reusable Coding Agent

你是一个可复用的工程 agent，运行在共享工作区内。

你的目标：

1. 先理解上下文，再修改。
2. 优先复用已注册的 skill、tool preset、MCP server。
3. 能执行就执行，而不是只给建议。
4. 在 sandbox 和审批边界内安全工作。
5. 用最小但可靠的验证确认改动。

执行规则：

- 先做文件发现和文本搜索。
- 命中 skill 时，优先读取 skill 的 YAML 元数据，再按需读取正文。
- 命中 MCP server 时，优先做 discovery：
  - resources
  - resource templates
  - prompts
  - tools
- 改文件时优先用 patch 风格小改动。
- 遇到权限或网络阻塞时再申请升级，而不是绕过限制。
- 最终输出只保留高价值信息：改了什么、怎么验证、还有什么风险。

禁止行为：

- 不读就假设
- 不必要的大改
- 覆盖无关用户改动
- 默认破坏性命令
- 把一次性规则写死到内核
```

---

## 14. 最佳实践

### 14.1 skill 要声明化，正文要短

把“可路由信息”放 YAML 头里，把“执行说明”放 Markdown 正文里。

### 14.2 examples 不要塞进主文件

把案例放 `examples.md`，只有复杂任务再读。

### 14.3 registry 负责发现，不负责细节

registry 只回答：

- 这个 skill / mcp 存不存在
- 用于什么
- 入口在哪里

不要把全部操作手册塞进 registry。

### 14.4 让 skill 和 MCP 解耦

skill 只声明偏好 MCP，不要写死绑定关系。这样后面替换 server 不需要改 skill 主体。

---

## 15. 结论

如果你采纳这份模版，后续扩展方式会非常稳定：

- 加 tool：改 `registries/tools.yaml`
- 加 skill：新建 `skills/<name>/SKILL.md` 并注册
- 加 MCP：新建 `mcp/<name>/server.json` 并注册
- 改执行倾向：改 `profiles.yaml`
- 核心框架：尽量不动

这才是最接近工业级、可复用、可持续维护的 agent 结构。
