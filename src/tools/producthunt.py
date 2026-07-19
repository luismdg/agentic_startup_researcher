import httpx

from src.config import get_settings, mock_mode
from src.models.candidate import EvidenceItem
from src.models.pipeline import RawCandidate
from src.orchestration.web_research_agent import research_channel
from src.tools.base import mock_or_none, today_iso
from src.utils.tracing import trace_line

SOURCE = "producthunt"

_GRAPHQL_QUERY = """
query Search($term: String!) {
  posts(first: 5, order: NEWEST) {
    edges {
      node {
        name
        tagline
        description
        website
        votesCount
        makers { name }
      }
    }
  }
}
"""
# NOTE: Product Hunt's public GraphQL API doesn't support free-text search on
# the posts collection directly; a real integration would normally filter by
# topic slug. This issues the call structure for when a token is present.


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    if mock_mode(SOURCE):
        candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[producthunt] mock mode")
        return candidates, trace + fallback_trace

    settings = get_settings()
    if settings.openai_enabled:
        candidates, agent_trace = await research_channel(
            query, niche, "producthunt", filters_context, max_results=4, discovery_pass=discovery_pass
        )
        trace.extend(agent_trace)
        if candidates:
            return candidates, trace
        trace.append(trace_line("[producthunt] OpenAI agentic browsing returned nothing — trying next path"))

    if settings.producthunt_enabled:
        try:
            candidates = await _real_search(query, niche, discovery_pass, trace)
            return candidates, trace
        except Exception as exc:
            trace.append(trace_line(f"[producthunt] GraphQL API call failed ({exc})"))

    candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[producthunt] no real results")
    return candidates, trace + fallback_trace


async def _real_search(
    query: str, niche: str, discovery_pass: int, trace: list[str]
) -> list[RawCandidate]:
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.producthunt_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.producthunt.com/v2/api/graphql",
            headers=headers,
            json={"query": _GRAPHQL_QUERY, "variables": {"term": query}},
        )
        resp.raise_for_status()
        edges = resp.json()["data"]["posts"]["edges"]

    trace.append(trace_line(f"[producthunt] GraphQL API call for '{query}' returned {len(edges)} posts"))

    candidates = []
    for edge in edges:
        node = edge["node"]
        makers = node.get("makers") or []
        candidates.append(
            RawCandidate(
                founder_name=makers[0]["name"] if makers else "Unknown maker",
                startup_name=node.get("name", "Unknown"),
                website=node.get("website"),
                niche=niche,
                one_line_description=(node.get("tagline") or node.get("description") or "")[:280],
                product_stage="launched",
                source_channel="Product Hunt",
                search_queries_used=[query],
                discovery_signals=[f"Product Hunt launch, {node.get('votesCount', 0)} votes"],
                discovery_pass=discovery_pass,
                evidence=[
                    EvidenceItem(
                        source_url=node.get("website", ""),
                        snippet=(node.get("tagline") or "")[:200],
                        date_captured=today_iso(),
                    )
                ],
                date_found=today_iso(),
            )
        )
    return candidates
