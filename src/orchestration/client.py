from functools import lru_cache

from openai import AsyncOpenAI

from src.config import get_settings

RESEARCH_MODEL = "gpt-4o-mini"
EXTRACTION_MODEL = "gpt-4o-mini"


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)
