import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """OPENAI_API_KEY is the only configurable credential. With it set, every
    channel except the already-free GitHub/arXiv/Reddit gets real agentic
    web browsing (see src/orchestration/). Without it, those channels read
    from synthetic mock data instead — GitHub/arXiv/Reddit still attempt
    their free, keyless real APIs regardless."""

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def mock_mode(source: str) -> bool:
    """Whether `source` has no real path available at all, and must fall
    back to synthetic mock data. arxiv/reddit/github are always real
    (free, keyless); every other source needs OPENAI_API_KEY for real
    agentic browsing."""
    if source in {"arxiv", "reddit", "github"}:
        return False
    return not get_settings().openai_enabled
