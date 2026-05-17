---
id: skill.local-explainer
name: Local Explainer
version: 1.0.0
category: learning
summary: >
  优先基于本地仓库中的模板、配置和说明文件解释 skill、MCP 和 agent 运行链路。
tags:
  - learning
  - local-context
  - explanation
triggers:
  explicit_mentions:
    - "@local-explainer"
  task_patterns:
    - "解释这个项目"
    - "skill 是什么"
    - "mcp 是什么"
    - "怎么看运行链路"
inputs:
  required: []
  optional:
    - focus_files
tools:
  required:
    - skill_discovery
  optional: []
mcp:
  preferred_servers: []
routing:
  priority: 90
  when_to_use: >
    当问题可以直接从当前仓库里的文档、registry 和代码得到答案时使用。
  when_not_to_use: >
    当问题明显依赖最新公开信息时，不要停留在本地解释。
safety:
  requires_escalation: false
  destructive_risk: low
outputs:
  produces:
    - answer
    - reasoning_summary
disclosure:
  strategy: progressive
  read_order:
    - summary
    - workflow
    - decision_rules
---

# Local Explainer

## Purpose

优先用仓库内已有内容回答问题，帮助用户理解 template、skill、MCP 和 host runtime 的关系。

## Workflow

1. 先识别用户是不是在问本项目本身。
2. 读取最相关的 registry、skill 文件和运行时代码。
3. 在不依赖联网的前提下回答。
4. 如果本地信息不足，再把任务让渡给 `web-researcher`。

## Decision Rules

- 能从本地文件回答，就不要调用 MCP。
- 回答时优先解释职责边界，而不是罗列文件清单。
- 如果引用代码，说明它在整个链路中的位置。
