import json
from urllib.parse import urlencode

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('web-search', json_response=True)


async def search_duckduckgo(query: str, limit: int) -> list[dict[str, str | int]]:
    params = urlencode({'q': query})
    url = f'https://html.duckduckgo.com/html/?{params}'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AgenticRAG/1.0',
        'accept': 'text/html,application/xhtml+xml'
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    results: list[dict[str, str | int]] = []

    for index, element in enumerate(soup.select('.result'), start=1):
        if len(results) >= limit:
            break

        link = element.select_one('.result__title a')
        snippet = element.select_one('.result__snippet')

        if link is None:
            continue

        title = link.get_text(strip=True)
        href = link.get('href', '')
        snippet_text = snippet.get_text(strip=True) if snippet else ''

        if not title or not href:
            continue

        results.append({
            'index': index,
            'title': title,
            'url': href,
            'snippet': snippet_text
        })

    return results


@mcp.tool(
    description='Search public web pages and return compact result snippets.'
)
async def web_search(query: str, limit: int = 5) -> str:
    results = await search_duckduckgo(query, limit)
    payload = {
        'query': query,
        'results': results
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    mcp.run(transport='stdio')
