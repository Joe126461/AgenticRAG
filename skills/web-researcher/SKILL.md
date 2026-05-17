---
id: skill.web-researcher
name: Web Researcher
version: 1.0.0
category: learning
summary: >
  当问题需要最新公开信息时，通过 MCP 的 `web-search` 工具获取网页结果，再结合本地上下文回答。
tags:
  - learning
  - mcp
  - web-search
triggers:
  explicit_mentions:
    - "@web-researcher"
    - "@mcp"
  task_patterns:
    - "最新"
    - "最近"
    - "联网搜索"
    - "查资料"
    - "搜索网页"
inputs:
  required: []
  optional:
    - freshness_requirement
tools:
  required:
    - mcp_discovery
  optional: []
mcp:
  preferred_servers:
    - web-search
routing:
  priority: 120
  when_to_use: >
    当问题依赖当前互联网信息、模型训练外的新资料或外部文档时使用。
  when_not_to_use: >
    当仓库内已经有足够答案时，不要把 web search 当作默认动作。
safety:
  requires_escalation: false
  destructive_risk: low
outputs:
  produces:
    - answer
    - sources
    - tool_trace
disclosure:
  strategy: progressive
  read_order:
    - summary
    - workflow
    - decision_rules
---

# Web Researcher

## Purpose

把 MCP 当成工具网关来使用，让模型先发现工具，再按需调用 `web_search`。

## Workflow

1. 先确认问题是否真的需要最新公开信息。
2. 发现 `web-search` MCP 提供的工具定义。
3. 把工具 schema 暴露给模型，由模型决定是否调用。
4. 用工具结果补全最终答案，并标出来源。

## Decision Rules

- 只有在问题需要新鲜信息时才调用 `web_search`。
- 优先返回少量高质量结果，而不是堆很多链接。
- 最终答案里要区分“模型推理”和“工具返回的事实”。
