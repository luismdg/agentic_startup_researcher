"""Node 4 — Multi-Source Fetch (fan-out to src/tools/*, in parallel) and
Node 5 — Raw Candidate Pool (trivial, URL/name-level dedup only; the real
similarity-based dedup is Node 6)."""

import asyncio

from src.models.pipeline import RawCandidate
from src.tools import accelerators, arxiv, github, google, linkedin, producthunt, reddit, twitter, youtube
from src.utils.similarity import normalize_domain
from src.utils.tracing import trace_line

TOOL_MAP = {
    "google": google.search,
    "github": github.search,
    "linkedin": linkedin.search,
    "arxiv": arxiv.search,
    "producthunt": producthunt.search,
    "accelerators": accelerators.search,
    "youtube": youtube.search,
    "twitter": twitter.search,
    "reddit": reddit.search,
}


async def fetch(
    queries: dict[str, list[str]], niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    calls = []
    call_labels = []

    for source, source_queries in queries.items():
        tool = TOOL_MAP.get(source)
        if not tool:
            trace.append(trace_line(f"Node 4 (multi_source_fetch): unknown source '{source}' skipped"))
            continue
        for q in source_queries:
            calls.append(tool(q, niche, discovery_pass, filters_context))
            call_labels.append((source, q))

    results = await asyncio.gather(*calls, return_exceptions=True)

    all_candidates: list[RawCandidate] = []
    for (source, q), result in zip(call_labels, results):
        if isinstance(result, BaseException):
            trace.append(trace_line(f"Node 4: [{source}] query '{q}' raised {result!r} — skipped"))
            continue
        candidates, tool_trace = result
        trace.extend(tool_trace)
        trace.append(trace_line(f"Node 4: [{source}] query '{q}' -> {len(candidates)} candidate(s)"))
        all_candidates.extend(candidates)

    return all_candidates, trace


def trivial_pool_dedup(candidates: list[RawCandidate]) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    seen_domains: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    pooled: list[RawCandidate] = []

    for c in candidates:
        domain = normalize_domain(c.website) if c.website else None
        pair_key = (c.startup_name.strip().casefold(), c.founder_name.strip().casefold())

        if domain and domain in seen_domains:
            trace.append(trace_line(f"Node 5 (raw_candidate_pool): dropped exact URL duplicate '{c.startup_name}'"))
            continue
        if not domain and pair_key in seen_pairs:
            trace.append(trace_line(f"Node 5: dropped exact name duplicate '{c.startup_name}'"))
            continue

        if domain:
            seen_domains.add(domain)
        seen_pairs.add(pair_key)
        pooled.append(c)

    return pooled, trace
