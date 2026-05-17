# Add MCP

1. 先确认这个能力为什么不该直接写进 host runtime，而应该独立成 MCP server。
2. 新建 `mcp/<server-name>/server.json` 和对应的 server 实现。
3. 在 `registries/mcp-servers.yaml` 注册 transport、capabilities 和 `use_when`。
4. 只在相关 skill 里把它放进 `preferred_servers`，不要所有 skill 都默认挂上它。
