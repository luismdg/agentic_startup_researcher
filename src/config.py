import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Optional credentials, read from a local .env file (see .env.example)
    or the OS environment directly. Every source works with none of these
    set — OPENAI_API_KEY is the headline one: it upgrades every channel
    except the already-free GitHub/arXiv/Reddit from mock to real agentic
    web browsing (see src/orchestration/). Set GENUINE_RESULTS_ONLY=true to
    disable mock fallback entirely — sources with no real capability, or
    whose real call fails, then return nothing rather than fabricated data."""

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    google_cse_id: str | None = os.getenv("GOOGLE_CSE_ID")
    producthunt_token: str | None = os.getenv("PRODUCTHUNT_TOKEN")
    youtube_api_key: str | None = os.getenv("YOUTUBE_API_KEY")
    genuine_only: bool = os.getenv("GENUINE_RESULTS_ONLY", "false").strip().lower() in ("1", "true", "yes")

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_api_key and self.google_cse_id)

    @property
    def github_enabled(self) -> bool:
        # GitHub's search API works unauthenticated (rate-limited); a token
        # just raises the rate limit, so "real mode" only needs the API to be
        # reachable, not a token specifically.
        return True

    @property
    def producthunt_enabled(self) -> bool:
        return bool(self.producthunt_token)

    @property
    def youtube_enabled(self) -> bool:
        return bool(self.youtube_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def mock_mode(source: str) -> bool:
    """Whether `source` has NO real path available at all (neither the
    OpenAI web-research agent nor a provider-specific API), and must fall
    back to synthetic mock data. linkedin/accelerators/twitter have no
    provider-specific public API in this build, but OPENAI_API_KEY still
    unlocks them via real agentic browsing. arxiv/reddit are always real
    (free, keyless — Reddit's public search.json endpoint needs no auth).
    Individual tools decide which real path to try first when this returns
    False — see src/tools/*.py."""
    settings = get_settings()
    always_real = {"arxiv", "reddit"}
    openai_only = {"linkedin", "accelerators", "twitter"}
    if source in always_real:
        return False
    if source in openai_only:
        return not settings.openai_enabled
    if source == "google":
        return not (settings.openai_enabled or settings.google_enabled)
    if source == "github":
        return not settings.github_enabled
    if source == "producthunt":
        return not (settings.openai_enabled or settings.producthunt_enabled)
    if source == "youtube":
        return not (settings.openai_enabled or settings.youtube_enabled)
    return True
