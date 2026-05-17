import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.agent.paths import WORKSPACE_ROOT
from app.agent.registry import load_mcp_registry, load_mcp_server_config


def _get_inherited_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if isinstance(value, str)
    }


@asynccontextmanager
async def mcp_client(server_id: str) -> AsyncIterator[dict[str, Any]]:
    registry = load_mcp_registry()
    server_entry = next((server for server in registry if server['id'] == server_id), None)

    if server_entry is None:
        raise ValueError(f'Unknown MCP server: {server_id}')

    server_config = load_mcp_server_config(server_entry)
    server_params = StdioServerParameters(
        command=server_config['command'],
        args=server_config.get('args', []),
        env=_get_inherited_env(),
        cwd=str(WORKSPACE_ROOT)
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            yield {
                'session': session,
                'server_entry': server_entry,
                'server_config': server_config
            }


async def discover_mcp_tools(server_id: str) -> dict[str, Any]:
    async with mcp_client(server_id) as state:
        session = state['session']
        server_entry = state['server_entry']
        result = await session.list_tools()

        return {
            'server_id': server_entry['id'],
            'server_name': server_entry['name'],
            'tools': [tool.model_dump(mode='json') for tool in result.tools]
        }


def _extract_text_content(content: list[Any]) -> str:
    parts: list[str] = []

    for item in content:
        text = getattr(item, 'text', None)
        if text:
            parts.append(text)

    return '\n'.join(parts).strip()


async def call_mcp_tool(server_id: str, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    async with mcp_client(server_id) as state:
        session = state['session']
        server_entry = state['server_entry']
        result = await session.call_tool(tool_name, args)

        return {
            'server_id': server_entry['id'],
            'server_name': server_entry['name'],
            'tool_name': tool_name,
            'args': args,
            'raw_result': result.model_dump(mode='json'),
            'text': _extract_text_content(result.content or [])
        }
