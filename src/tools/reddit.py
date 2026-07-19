import httpx

from src.config import mock_mode
from src.models.candidate import EvidenceItem
from src.models.pipeline import RawCandidate
from src.orchestration.web_research_agent import research_channel
from src.tools.base import mock_or_none, today_iso
from src.utils.tracing import trace_line

SOURCE = "reddit"

# Reddit's public search.json endpoint needs no auth (like GitHub/arXiv), so
# that's the first real path — it's fast and free. The OpenAI agent (for
# accounts where the JSON endpoint is blocked/rate-limited) is the fallback,
# then mock.


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    if mock_mode(SOURCE):
        candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[reddit] mock mode")
        return candidates, trace + fallback_trace

    try:
        candidates = await _real_search(query, niche, discovery_pass, trace)
        if candidates:
            return candidates, trace
        trace.append(trace_line("[reddit] search.json returned nothing — trying next path"))
    except Exception as exc:
        trace.append(trace_line(f"[reddit] search.json call failed ({exc}) — trying next path"))

    candidates, agent_trace = await research_channel(
        query, niche, "reddit", filters_context, max_results=4, discovery_pass=discovery_pass
    )
    trace.extend(agent_trace)
    if candidates:
        return candidates, trace

    trace.append(trace_line("[reddit] OpenAI agentic browsing returned nothing"))
    candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[reddit] no real results")
    return candidates, trace + fallback_trace


async def _real_search(
    query: str, niche: str, discovery_pass: int, trace: list[str]
) -> list[RawCandidate]:
    headers = {"User-Agent": "vc-brain-sourcing-agent/1.0"}
    params = {"q": query, "sort": "new", "limit": 5}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://www.reddit.com/search.json", headers=headers, params=params
        )
        resp.raise_for_status()
        posts = resp.json().get("data", {}).get("children", [])

    trace.append(trace_line(f"[reddit] search.json call for '{query}' returned {len(posts)} posts"))

    candidates = []
    for post in posts:
        data = post.get("data", {})
        title = data.get("title") or "Untitled post"
        author = data.get("author") or "unknown redditor"
        permalink = data.get("permalink")
        url = f"https://reddit.com{permalink}" if permalink else data.get("url", "")
        candidates.append(
            RawCandidate(
                # Reddit posts are pseudonymous — the founder's real name
                # usually isn't in the post itself, a genuine source limit.
                founder_name=f"u/{author}",
                startup_name=title[:80],
                website=data.get("url") if data.get("url", "").count("reddit.com") == 0 else None,
                niche=niche,
                one_line_description=(data.get("selftext") or title)[:280],
                source_channel="Community",
                search_queries_used=[query],
                discovery_signals=[f"Reddit post in r/{data.get('subreddit', 'unknown')}"],
                discovery_pass=discovery_pass,
                evidence=[
                    EvidenceItem(source_url=url, snippet=title[:200], date_captured=today_iso())
                ],
                date_found=today_iso(),
            )
        )
    return candidates
