import pytest

import src.nodes.dedup_similarity as dedup_module
import src.nodes.pipeline as pipeline_module
import src.nodes.query_generation as query_generation_module
import src.orchestration.localization as localization_module
import src.tools.accelerators as accelerators_tool
import src.tools.arxiv as arxiv_tool
import src.tools.base as tools_base_module
import src.tools.github as github_tool
import src.tools.google as google_tool
import src.tools.linkedin as linkedin_tool
import src.tools.producthunt as producthunt_tool
import src.tools.reddit as reddit_tool
import src.tools.twitter as twitter_tool
import src.tools.youtube as youtube_tool
import src.utils.similarity as similarity_module


class _FakeSettings:
    openai_enabled = False
    openai_api_key = None
    genuine_only = False  # tests rely on mock fallback data being available


# A fixed snapshot, independent of the real (mutable) known-startups.json —
# that file grows as the app is actually used, which would otherwise make
# these tests flaky/order-dependent on whatever's been searched for so far.
_KNOWN_STARTUPS_SNAPSHOT = [
    {
        "startup_name": "FyTic",
        "website": "https://fytic.mx",
        "founder_name": "Luis Ramírez",
        "niche": "Mexican LegalTech",
        "one_line_description": "Billing and invoicing automation for Mexican law firms.",
        "first_seen": "2026-07-10",
    },
    {
        "startup_name": "Improvider Legal Tech",
        "website": "https://improvider.io",
        "founder_name": "Diego Salcido",
        "niche": "Mexican LegalTech",
        "one_line_description": "Contract lifecycle management platform for corporate legal teams.",
        "first_seen": "2026-07-09",
    },
]


@pytest.fixture(autouse=True)
def hermetic_mock_mode(monkeypatch):
    """Tests must be offline and deterministic. This forces every tool into
    mock mode — including github/arxiv, which attempt a real call by default
    since they're free/keyless — and disables the optional OpenAI-assisted
    paths regardless of what's in the developer's local .env."""
    monkeypatch.setattr(github_tool, "mock_mode", lambda source: True)
    monkeypatch.setattr(google_tool, "mock_mode", lambda source: True)
    monkeypatch.setattr(producthunt_tool, "mock_mode", lambda source: True)
    monkeypatch.setattr(linkedin_tool, "mock_mode", lambda source: True)
    monkeypatch.setattr(accelerators_tool, "mock_mode", lambda source: True)
    monkeypatch.setattr(youtube_tool, "mock_mode", lambda source: True)
    monkeypatch.setattr(twitter_tool, "mock_mode", lambda source: True)
    monkeypatch.setattr(reddit_tool, "mock_mode", lambda source: True)

    async def _network_disabled(*args, **kwargs):
        raise RuntimeError("network disabled in tests")

    monkeypatch.setattr(arxiv_tool, "_real_search", _network_disabled)
    monkeypatch.setattr(similarity_module, "get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(query_generation_module, "get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(localization_module, "get_settings", lambda: _FakeSettings())
    # regardless of the developer's real .env (e.g. GENUINE_RESULTS_ONLY=true
    # locally), tests need mock fallback to actually produce data by default —
    # the dedicated genuine-only tests override this again within themselves
    monkeypatch.setattr(tools_base_module, "get_settings", lambda: _FakeSettings())
    # don't let test runs mutate the real known-startups.json memory file
    monkeypatch.setattr(pipeline_module, "append_known_startups", lambda entries: None)
    # dedup against a fixed snapshot instead of the real, growing memory file
    monkeypatch.setattr(dedup_module, "load_known_startups", lambda: _KNOWN_STARTUPS_SNAPSHOT)
