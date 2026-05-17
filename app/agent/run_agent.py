import json
from typing import Any

from app.agent.mcp_client import call_mcp_tool, discover_mcp_tools
from app.agent.openai_client import create_openai_client, get_model_config
from app.agent.registry import (
    load_agent_contract,
    load_registry_summary,
    load_skill_definition,
    load_skills_registry,
    to_display_path
)
from app.agent.router import select_skill


def to_prompt_block(title: str, value: str) -> str:
    return f'## {title}\n{value}'


def normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue

            text = getattr(item, 'text', None)
            if text:
                parts.append(text)
                continue

            if isinstance(item, dict) and item.get('text'):
                parts.append(item['text'])
                continue

            parts.append(json.dumps(item, ensure_ascii=False))

        return '\n'.join(parts)

    if content is None:
        return ''

    return json.dumps(content, ensure_ascii=False)


def build_system_prompt(
    *,
    agent_contract: str,
    skill_definition: dict[str, Any],
    discovered_tools: list[dict[str, Any]]
) -> str:
    front_matter = json.dumps(skill_definition['front_matter'], ensure_ascii=False, indent=2)
    discovered_tool_summary = (
        json.dumps(discovered_tools, ensure_ascii=False, indent=2)
        if discovered_tools
        else 'No MCP tools discovered for this turn.'
    )

    return '\n\n'.join([
        agent_contract,
        to_prompt_block('Selected Skill Metadata', front_matter),
        to_prompt_block('Selected Skill Body', skill_definition['body']),
        to_prompt_block('Discovered MCP Tools', discovered_tool_summary),
        to_prompt_block(
            'Response Requirements',
            '\n'.join([
                '- 默认用中文回答。',
                '- 先回答用户问题，再补充必要解释。',
                '- 只有在问题确实需要最新公开信息时才调用工具。',
                '- 如果调用了工具，在结尾添加一个简短的 `Execution Trace` 段落。'
            ])
        )
    ])


def to_openai_tools(discovered_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    openai_tools: list[dict[str, Any]] = []

    for server in discovered_tools:
        for tool in server.get('tools', []):
            openai_tools.append({
                'type': 'function',
                'function': {
                    'name': tool['name'],
                    'description': tool.get('description') or f"Tool from MCP server {server['server_id']}",
                    'parameters': tool.get('inputSchema') or {
                        'type': 'object',
                        'properties': {}
                    }
                }
            })

    return openai_tools


def build_tool_lookup(discovered_tools: list[dict[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}

    for server in discovered_tools:
        for tool in server.get('tools', []):
            lookup[tool['name']] = server['server_id']

    return lookup


def parse_tool_arguments(raw_arguments: Any) -> dict[str, Any]:
    if not raw_arguments:
        return {}

    if isinstance(raw_arguments, dict):
        return raw_arguments

    try:
        return json.loads(raw_arguments)
    except json.JSONDecodeError as error:
        return {
            'raw': raw_arguments,
            'parseError': str(error)
        }


async def discover_preferred_tools(skill_definition: dict[str, Any]) -> list[dict[str, Any]]:
    preferred_servers = skill_definition.get('mcp_preferred', [])
    discoveries: list[dict[str, Any]] = []

    for server_id in preferred_servers:
        discoveries.append(await discover_mcp_tools(server_id))

    return discoveries


async def complete_chat(
    *,
    client: Any,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]]
) -> Any:
    return await client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=messages,
        tools=tools or None,
        tool_choice='auto' if tools else None
    )


async def run_agent_turn(question: str) -> dict[str, Any]:
    agent_contract = load_agent_contract()
    skill_entries = load_skills_registry()
    registry_summary = load_registry_summary()
    selected_skill = select_skill(question, skill_entries)
    skill_definition = load_skill_definition(selected_skill)
    discovered_tools = await discover_preferred_tools(skill_definition)
    openai_tools = to_openai_tools(discovered_tools)
    tool_lookup = build_tool_lookup(discovered_tools)
    model_config = get_model_config()
    client = create_openai_client()
    messages: list[dict[str, Any]] = [
        {
            'role': 'system',
            'content': build_system_prompt(
                agent_contract=agent_contract,
                skill_definition=skill_definition,
                discovered_tools=discovered_tools
            )
        },
        {
            'role': 'user',
            'content': question
        }
    ]
    trace = {
        'model': model_config['model'],
        'selectedSkill': {
            'id': selected_skill['id'],
            'name': selected_skill['name'],
            'file': to_display_path(skill_definition['absolute_path'])
        },
        'discoveredTools': [
            {
                'serverId': server['server_id'],
                'serverName': server['server_name'],
                'tools': [tool['name'] for tool in server.get('tools', [])]
            }
            for server in discovered_tools
        ],
        'toolCalls': [],
        'registrySummary': registry_summary
    }

    first_pass = await complete_chat(
        client=client,
        model=model_config['model'],
        messages=messages,
        tools=openai_tools
    )
    assistant_message = first_pass.choices[0].message if first_pass.choices else None

    if assistant_message is None:
        raise RuntimeError('The model returned an empty response.')

    first_pass_text = normalize_content(assistant_message.content)
    tool_calls = assistant_message.tool_calls or []

    if not tool_calls:
        return {
            'answer': first_pass_text,
            'trace': trace
        }

    messages.append({
        'role': 'assistant',
        'content': first_pass_text,
        'tool_calls': [tool_call.model_dump(mode='json') for tool_call in tool_calls]
    })

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        server_id = tool_lookup.get(tool_name)

        if server_id is None:
            continue

        args = parse_tool_arguments(tool_call.function.arguments)
        tool_result = await call_mcp_tool(server_id, tool_name, args)
        trace['toolCalls'].append({
            'serverId': server_id,
            'toolName': tool_name,
            'arguments': args,
            'resultPreview': tool_result['text'][:500]
        })
        messages.append({
            'role': 'tool',
            'tool_call_id': tool_call.id,
            'content': tool_result['text'] or json.dumps(tool_result['raw_result'], ensure_ascii=False)
        })

    second_pass = await complete_chat(
        client=client,
        model=model_config['model'],
        messages=messages,
        tools=openai_tools
    )
    final_message = second_pass.choices[0].message if second_pass.choices else None

    return {
        'answer': normalize_content(final_message.content if final_message else ''),
        'trace': trace
    }
