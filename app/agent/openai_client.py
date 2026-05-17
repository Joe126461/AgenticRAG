from openai import AsyncOpenAI


def get_model_config() -> dict[str, str]:
    from os import getenv

    return {
        'base_url': getenv('VLLM_BASE_URL', 'http://localhost:8000/v1'),
        'model': getenv('MODEL_NAME', 'Qwen/Qwen2.5-7B-Instruct-AWQ'),
        'api_key': getenv('OPENAI_API_KEY', 'local')
    }


def create_openai_client() -> AsyncOpenAI:
    config = get_model_config()

    return AsyncOpenAI(
        api_key=config['api_key'],
        base_url=config['base_url']
    )
