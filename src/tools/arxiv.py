from xml.etree import ElementTree

import httpx

from src.models.candidate import EvidenceItem
from src.models.pipeline import RawCandidate
from src.tools.base import mock_or_none, today_iso
from src.utils.tracing import trace_line

SOURCE = "arxiv"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    """arXiv's Atom API is free and keyless, so this is always a real call —
    there's no mock/real split here, unlike the other tools."""
    trace: list[str] = []
    try:
        candidates = await _real_search(query, niche, discovery_pass, trace)
        return candidates, trace
    except Exception as exc:
        trace.append(trace_line(f"[arxiv] real API call failed ({exc})"))
        candidates, fallback_trace = mock_or_none(SOURCE, niche, query, discovery_pass, "[arxiv] real call failed")
        return candidates, trace + fallback_trace


async def _real_search(
    query: str, niche: str, discovery_pass: int, trace: list[str]
) -> list[RawCandidate]:
    params = {"search_query": f"all:{query}", "start": 0, "max_results": 5}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("http://export.arxiv.org/api/query", params=params)
        resp.raise_for_status()
        body = resp.text

    root = ElementTree.fromstring(body)
    entries = root.findall(f"{ATOM_NS}entry")
    trace.append(trace_line(f"[arxiv] real search for '{query}' returned {len(entries)} preprints"))

    candidates = []
    for entry in entries:
        title = (entry.findtext(f"{ATOM_NS}title") or "Untitled preprint").strip()
        summary = (entry.findtext(f"{ATOM_NS}summary") or "").strip()
        link = entry.findtext(f"{ATOM_NS}id") or ""
        published = (entry.findtext(f"{ATOM_NS}published") or "")[:10]
        authors = [
            (a.findtext(f"{ATOM_NS}name") or "Unknown author").strip()
            for a in entry.findall(f"{ATOM_NS}author")
        ]
        founder_name = authors[0] if authors else "Unknown author"

        candidates.append(
            RawCandidate(
                founder_name=founder_name,
                startup_name=f"{title[:60]} (unnamed project)",
                website=None,
                estimated_founded_year=None,
                niche=niche,
                one_line_description=summary[:280] or title,
                product_stage="idea",
                team_size_estimate=1,
                source_channel="Academic papers",
                search_queries_used=[query],
                discovery_signals=[f"arXiv preprint '{title}' published {published or 'recently'}"],
                discovery_pass=discovery_pass,
                evidence=[
                    EvidenceItem(source_url=link, snippet=summary[:200], date_captured=today_iso())
                ],
                date_found=today_iso(),
            )
        )
    return candidates
