from src.config import get_settings, mock_mode
from src.models.pipeline import RawCandidate
from src.orchestration.web_research_agent import research_channel
from src.tools.base import mock_candidates_for
from src.utils.tracing import trace_line

SOURCE = "producthunt"


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    if mock_mode(SOURCE):
        return mock_candidates_for(SOURCE, niche, query, discovery_pass), trace

    settings = get_settings()
    if settings.openai_enabled:
        candidates, agent_trace = await research_channel(
            query, niche, "producthunt", filters_context, max_results=4, discovery_pass=discovery_pass
        )
        trace.extend(agent_trace)
        if candidates:
            return candidates, trace
        trace.append(trace_line("[producthunt] OpenAI agentic browsing returned nothing — falling back to mock data"))

    return mock_candidates_for(SOURCE, niche, query, discovery_pass), trace
