import json
from pathlib import Path
from typing import Any

import frontmatter
import yaml

from app.agent.paths import WORKSPACE_ROOT, resolve_workspace_path


def _read_text(relative_path: str) -> str:
    return resolve_workspace_path(relative_path).read_text(encoding='utf-8')


def _read_yaml(relative_path: str) -> dict[str, Any]:
    content = _read_text(relative_path)
    data = yaml.safe_load(content)

    return data or {}


def _to_relative_path(value: str) -> str:
    return value.removeprefix('./')


def load_agent_contract() -> str:
    return _read_text('AGENT.md')


def load_tool_registry() -> dict[str, Any]:
    return _read_yaml('registries/tools.yaml').get('tool_presets', {})


def load_skills_registry() -> list[dict[str, Any]]:
    return _read_yaml('registries/skills.yaml').get('skills', [])


def load_mcp_registry() -> list[dict[str, Any]]:
    return _read_yaml('registries/mcp-servers.yaml').get('mcp_servers', [])


def load_skill_definition(skill_entry: dict[str, Any]) -> dict[str, Any]:
    relative_path = _to_relative_path(skill_entry['path'])
    absolute_path = resolve_workspace_path(relative_path)
    parsed = frontmatter.load(absolute_path)

    return {
        **skill_entry,
        'absolute_path': absolute_path,
        'front_matter': parsed.metadata,
        'body': parsed.content.strip()
    }


def load_mcp_server_config(server_entry: dict[str, Any]) -> dict[str, Any]:
    relative_path = _to_relative_path(server_entry['config_path'])
    absolute_path = resolve_workspace_path(relative_path)
    content = absolute_path.read_text(encoding='utf-8')

    return {
        **json.loads(content),
        'absolute_path': absolute_path
    }


def load_registry_summary() -> dict[str, Any]:
    skills = load_skills_registry()
    mcp_servers = load_mcp_registry()

    return {
        'skills': [
            {
                'id': skill['id'],
                'name': skill['name'],
                'summary': skill['summary'],
                'preferredMcp': skill.get('mcp_preferred', [])
            }
            for skill in skills
        ],
        'mcpServers': [
            {
                'id': server['id'],
                'name': server['name'],
                'purpose': server['purpose'],
                'transport': server['transport']
            }
            for server in mcp_servers
        ]
    }


def to_display_path(absolute_path: Path) -> str:
    return absolute_path.relative_to(WORKSPACE_ROOT).as_posix()
