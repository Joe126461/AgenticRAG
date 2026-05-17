# Add Skill

1. 先想清楚这个 skill 只解决哪一类问题，保持它足够窄。
2. 新建 `skills/<skill-name>/SKILL.md`，用 YAML front matter 写清 `triggers`、`tools`、`mcp` 和 `outputs`。
3. 在 `registries/skills.yaml` 注册入口，给它一个简短摘要和优先级。
4. 只有当本地上下文不足时，才在 skill 里声明 `preferred_servers`。
