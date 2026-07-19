import httpx

from src.config import get_settings, mock_mode
from src.models.candidate import EvidenceItem
from src.models.pipeline import RawCandidate
from src.orchestration.web_research_agent import research_channel
from src.tools.base import mock_or_none, today_iso
from src.utils.tracing import trace_line

SOURCE = "google"


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    if mock_mode(SOURCE):
        candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[google] mock mode")
        return candidates, trace + fallback_trace

    settings = get_settings()
    if settings.openai_enabled:
        candidates, agent_trace = await research_channel(
            query, niche, "google", filters_context, max_results=4, discovery_pass=discovery_pass
        )
        trace.extend(agent_trace)
        if candidates:
            return candidates, trace
        trace.append(trace_line("[google] OpenAI agentic browsing returned nothing — trying next path"))

    if settings.google_enabled:
        try:
            candidates = await _real_search(query, niche, discovery_pass, trace)
            return candidates, trace
        except Exception as exc:
            trace.append(trace_line(f"[google] Custom Search API call failed ({exc})"))

    candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[google] no real results")
    return candidates, trace + fallback_trace


async def _real_search(
    query: str, niche: str, discovery_pass: int, trace: list[str]
) -> list[RawCandidate]:
    settings = get_settings()
    params = {
        "key": settings.google_api_key,
        "cx": settings.google_cse_id,
        "q": query,
        "num": 5,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://www.googleapis.com/customsearch/v1", params=params)
        resp.raise_for_status()
        items = resp.json().get("items", [])

    trace.append(trace_line(f"[google] Custom Search API call for '{query}' returned {len(items)} results"))

    candidates = []
    for item in items:
        title = item.get("title", "Unknown")
        candidates.append(
            RawCandidate(
                # Raw web search results have no structured founder identity —
                # this is a genuine limitation of the source, not a bug; it
                # naturally pulls confidence down in Node 9.
                founder_name="Unknown — needs verification",
                startup_name=title[:80],
                website=item.get("link"),
                niche=niche,
                one_line_description=(item.get("snippet") or "")[:280],
                source_channel="Google search",
                search_queries_used=[query],
                discovery_signals=[f"Surfaced by web search for '{query}'"],
                discovery_pass=discovery_pass,
                evidence=[
                    EvidenceItem(
                        source_url=item.get("link", ""),
                        snippet=(item.get("snippet") or "")[:200],
                        date_captured=today_iso(),
                    )
                ],
                date_found=today_iso(),
            )
        )
    return candidates
