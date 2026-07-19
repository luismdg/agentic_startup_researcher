from src.config import get_settings, mock_mode
from src.models.pipeline import RawCandidate
from src.orchestration.web_research_agent import research_channel
from src.tools.base import mock_or_none
from src.utils.tracing import trace_line

SOURCE = "accelerators"

# Accelerator cohort pages are scattered across dozens of individual sites
# with no common API — but OpenAI's hosted web-search tool can browse those
# pages directly, so OPENAI_API_KEY is what makes this channel real instead
# of a permanently-mock stub.


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    if mock_mode(SOURCE):
        candidates, fallback_trace = mock_or_none(
            SOURCE, niche, query, discovery_pass, "[accelerators] no OpenAI key configured"
        )
        return candidates, trace + fallback_trace

    settings = get_settings()
    if settings.openai_enabled:
        candidates, agent_trace = await research_channel(
            query, niche, "accelerators", filters_context, max_results=4, discovery_pass=discovery_pass
        )
        trace.extend(agent_trace)
        if candidates:
            return candidates, trace
        trace.append(trace_line("[accelerators] OpenAI agentic browsing returned nothing"))

    candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[accelerators] no real results")
    return candidates, trace + fallback_trace
