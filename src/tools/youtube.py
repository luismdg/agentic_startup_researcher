import httpx

from src.config import get_settings, mock_mode
from src.models.candidate import EvidenceItem
from src.models.pipeline import RawCandidate
from src.orchestration.web_research_agent import research_channel
from src.tools.base import mock_or_none, today_iso
from src.utils.tracing import trace_line

SOURCE = "youtube"

# Idea-stage founders show up here as "building in public" vlogs and demo
# videos long before there's a company site. OpenAI agentic browsing is
# tried first (it can watch for the channel's own vocabulary — see
# src/data/channel-vocabulary.json); YOUTUBE_API_KEY (Data API v3) is a
# structured alternate path.


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    if mock_mode(SOURCE):
        candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[youtube] mock mode")
        return candidates, trace + fallback_trace

    settings = get_settings()
    if settings.openai_enabled:
        candidates, agent_trace = await research_channel(
            query, niche, "youtube", filters_context, max_results=4, discovery_pass=discovery_pass
        )
        trace.extend(agent_trace)
        if candidates:
            return candidates, trace
        trace.append(trace_line("[youtube] OpenAI agentic browsing returned nothing — trying next path"))

    if settings.youtube_enabled:
        try:
            candidates = await _real_search(query, niche, discovery_pass, trace)
            return candidates, trace
        except Exception as exc:
            trace.append(trace_line(f"[youtube] Data API call failed ({exc})"))

    candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[youtube] no real results")
    return candidates, trace + fallback_trace


async def _real_search(
    query: str, niche: str, discovery_pass: int, trace: list[str]
) -> list[RawCandidate]:
    settings = get_settings()
    params = {
        "key": settings.youtube_api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "order": "date",
        "maxResults": 5,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://www.googleapis.com/youtube/v3/search", params=params)
        resp.raise_for_status()
        items = resp.json().get("items", [])

    trace.append(trace_line(f"[youtube] Data API call for '{query}' returned {len(items)} videos"))

    candidates = []
    for item in items:
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        candidates.append(
            RawCandidate(
                # A video's uploader channel name usually isn't the founder's
                # real name either — same genuine limitation as other raw
                # search sources; Node 9 reflects that in confidence.
                founder_name=snippet.get("channelTitle", "Unknown — needs verification"),
                startup_name=(snippet.get("title") or "Unknown")[:80],
                website=f"https://youtube.com/watch?v={video_id}" if video_id else None,
                niche=niche,
                one_line_description=(snippet.get("description") or "")[:280],
                source_channel="YouTube",
                search_queries_used=[query],
                discovery_signals=[f"YouTube video surfaced by search for '{query}'"],
                discovery_pass=discovery_pass,
                evidence=[
                    EvidenceItem(
                        source_url=f"https://youtube.com/watch?v={video_id}" if video_id else "",
                        snippet=(snippet.get("description") or "")[:200],
                        date_captured=today_iso(),
                    )
                ],
                date_found=today_iso(),
            )
        )
    return candidates
