# Add Tool

1. 区分清楚这是 host 自带工具，还是 MCP 暴露给模型的工具。
2. 如果是 host 侧能力，就在 `registries/tools.yaml` 里声明 preset。
3. 如果是给模型调用的能力，更适合放进 MCP server 并通过 discovery 暴露。
