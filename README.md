# Learning Agent with vLLM

This repository is now a minimal, learning-focused agent that demonstrates four layers working together:

1. `skills/` describe how the agent should behave for a narrow task.
2. `registries/` register which skills and MCP servers exist.
3. `mcp/web-search/` implements a real MCP stdio server.
4. `app/main.py` and `app/agent/` implement the host runtime that reads registries, selects a skill, discovers MCP tools, and calls a local model through vLLM.

## Why this model stack

For an RTX 4070 Ti Super with 16 GB VRAM, this project defaults to:

- `vLLM` for industrial, OpenAI-compatible serving
- `Qwen/Qwen2.5-7B-Instruct-AWQ` for a better fit on 16 GB VRAM

This is intentionally a general instruct model rather than a coder-specific variant, because current vLLM tool calling support is more predictable here and this project is focused on learning the host-skill-MCP flow.

The host runtime is now Python-first so that it is easier to extend later with:

- embeddings
- vector stores
- retrieval pipelines
- data processing and evaluation scripts

## Architecture

The request path is:

1. The browser sends a question to `POST /api/chat`.
2. The host runtime loads `AGENT.md`, `registries/skills.yaml`, and `registries/mcp-servers.yaml`.
3. The host selects a skill with a lightweight router.
4. If the selected skill prefers MCP servers, the host discovers MCP tools through the official MCP SDK.
5. The host passes the selected skill and discovered tool schemas to the model through the OpenAI-compatible vLLM API.
6. If the model emits tool calls, the host executes them through the local MCP stdio client.
7. The host sends tool results back to the model and returns the final answer and trace to the browser.

## Files to read first

- `AGENT.md`
- `registries/skills.yaml`
- `skills/local-explainer/SKILL.md`
- `skills/web-researcher/SKILL.md`
- `registries/mcp-servers.yaml`
- `mcp/web-search/server.json`
- `app/mcp/web_search_server.py`
- `app/agent/run_agent.py`
- `app/agent/mcp_client.py`

## Run locally without Docker

1. Start a vLLM OpenAI-compatible server separately.
2. Copy `.env.example` to `.env` if you want custom values.
3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Start the app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

5. Open [http://localhost:3000](http://localhost:3000)

## Run with Docker Compose

Prerequisites:

- Docker Desktop with WSL2 backend enabled
- NVIDIA drivers installed
- Docker GPU support working

Then run:

```bash
docker compose up --build
```

This starts:

- `vllm` on `http://localhost:8000`
- `app` on `http://localhost:3000`

## Python runtime shape

The browser still talks to the same endpoints, but the host runtime is now:

- `FastAPI` for the web server
- `AsyncOpenAI` for talking to the OpenAI-compatible vLLM server
- official `mcp` Python SDK for stdio client and server support

This keeps the inference layer industrial, while making the orchestration layer easier to extend with Python-native AI tooling later.

## Notes on vLLM

The compose file uses:

- `vllm/vllm-openai:latest`
- `--quantization awq`
- `--enable-auto-tool-choice`
- `--tool-call-parser hermes`

This is designed to keep the setup small while still showing an industrial serving pattern.
