from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import APIConnectionError
from pydantic import BaseModel

from app.agent.openai_client import get_model_config
from app.agent.paths import resolve_workspace_path
from app.agent.registry import load_registry_summary
from app.agent.run_agent import run_agent_turn


class ChatRequest(BaseModel):
    question: str


app = FastAPI(title='Learning Agent')
public_dir = resolve_workspace_path('public')


@app.get('/api/health')
async def health() -> dict[str, object]:
    return {
        'ok': True,
        'model': get_model_config()['model']
    }


@app.get('/api/registry-summary')
async def registry_summary() -> dict[str, object]:
    return {
        **load_registry_summary(),
        'model': get_model_config()
    }


@app.post('/api/chat')
async def chat(payload: ChatRequest) -> dict[str, object]:
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail='Question is required.')

    return await run_agent_turn(question)


@app.exception_handler(APIConnectionError)
async def handle_api_connection_error(request, exc: APIConnectionError) -> JSONResponse:
    model_config = get_model_config()

    return JSONResponse(
        status_code=500,
        content={
            'error': f"Could not reach vLLM at {model_config['base_url']}. Start the vLLM service and retry."
        }
    )


@app.exception_handler(HTTPException)
async def handle_http_error(request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.detail}
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={'error': str(exc) or 'Unexpected server error.'}
    )


app.mount('/', StaticFiles(directory=public_dir, html=True), name='static')


@app.get('/{full_path:path}')
async def frontend_fallback(full_path: str) -> FileResponse:
    return FileResponse(public_dir / 'index.html')
