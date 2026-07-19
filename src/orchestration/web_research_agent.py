"""The 'real agentic browsing' engine. Given a query, this actually browses
the live web via OpenAI's hosted web-search tool, then extracts structured
candidates from what it found. Two calls, not one: asking a tool-using
model to both browse AND emit strict JSON in the same turn is unreliable,
so step 1 (browse) gathers findings as free text with citations, and step 2
(extract) — a cheap, tool-free call — converts that into JSON matching
schemas.py. Any failure at either step degrades to an empty result, which
the calling tool (src/tools/*.py) then falls back to mock data for — same
contract every tool already follows.

The browse prompt is framed per-channel using src/data/channel-vocabulary.json
— the same underlying signal ("this is an early-stage startup") is worded
completely differently on LinkedIn ('Co-founder', 'MVP', 'Summit') than on
GitHub ('agentic', 'WIP', 'hackathon') or Reddit ('feedback wanted')."""

import json

from src.config import get_settings
from src.models.candidate import EvidenceItem
from src.models.pipeline import RawCandidate
from src.orchestration.client import EXTRACTION_MODEL, RESEARCH_MODEL, get_openai_client
from src.orchestration.schemas import EXTRACTION_INSTRUCTIONS
from src.services.data_store import load_channel_vocabulary
from src.tools.base import today_iso
from src.utils.tracing import trace_line

_CHANNEL_LABELS = {
    "google": "Google search",
    "linkedin": "Community",
    "producthunt": "Product Hunt",
    "accelerators": "Accelerators",
    "youtube": "YouTube",
    "twitter": "Twitter/X",
    "reddit": "Reddit",
}

# The exact hosted web-search tool name has shifted across OpenAI API
# versions/accounts ("web_search_preview" vs "web_search"); try both rather
# than betting on one and crashing if it's wrong for this account.
_WEB_SEARCH_TOOL_TYPES = ["web_search_preview", "web_search"]


def _build_framing(channel: str) -> str:
    """People signal 'early-stage startup' differently per channel — a
    LinkedIn headline says 'Co-founder', a GitHub repo says 'agentic'/'WIP',
    a Reddit post says 'feedback wanted'. Pulled from
    src/data/channel-vocabulary.json so both this prompt and Node 3's query
    wording stay in sync."""
    vocab = load_channel_vocabulary().get(channel, {})
    parts = [vocab.get("framing", "Search the general web for candidates.")]
    labels = vocab.get("typical_labels", [])
    if labels:
        parts.append(f"Typical terms/labels used on this channel: {', '.join(labels)}.")
    events = vocab.get("typical_events", [])
    if events:
        parts.append(f"Watch for mentions of: {', '.join(events)}.")
    site_hint = vocab.get("site_hint")
    if site_hint:
        parts.append(f"Include '{site_hint}' in your search terms to stay on this channel.")
    return " ".join(parts)


async def research_channel(
    query: str,
    niche: str,
    channel: str,
    filters_context: str,
    max_results: int,
    discovery_pass: int = 1,
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    settings = get_settings()
    if not settings.openai_enabled:
        return [], trace

    client = get_openai_client()
    framing = _build_framing(channel)
    capped = max(1, min(max_results, 4))

    prompt = (
        f"You are sourcing early-stage, low-visibility startup founders for a venture capital "
        f"scout, in the niche '{niche}'. {framing} Deliberately favor candidates with thin, "
        f"scattered, hard-to-find evidence over well-known, already-funded, heavily-covered "
        f"ones — the goal is finding founders BEFORE other investors notice them, not the most "
        f"famous names in the space."
        + (f" Additional context: {filters_context}" if filters_context else "")
        + f" Search query to start from: '{query}'. Find up to {capped} real, distinct "
        f"candidates. For each, note the founder's name (and every co-founder by name if the "
        f"source mentions more than one — don't just note 'the founders', list each person), "
        f"the startup name, a real source URL you found it at, and a short snippet/quote. If "
        f"you can't find enough genuinely real candidates, report fewer rather than inventing "
        f"any — never fabricate a candidate or URL."
    )

    findings_text, browse_trace = await _browse(client, prompt)
    trace.extend(browse_trace)
    if not findings_text:
        return [], trace

    try:
        candidates = await _extract(client, findings_text, niche, channel, query, discovery_pass)
        trace.append(
            trace_line(f"[{channel}] OpenAI research agent extracted {len(candidates)} candidate(s)")
        )
        return candidates, trace
    except Exception as exc:
        trace.append(trace_line(f"[{channel}] structured extraction failed ({exc})"))
        return [], trace


async def _browse(client, prompt: str) -> tuple[str, list[str]]:
    trace: list[str] = []
    for tool_type in _WEB_SEARCH_TOOL_TYPES:
        try:
            response = await client.responses.create(
                model=RESEARCH_MODEL,
                input=prompt,
                tools=[{"type": tool_type}],
            )
            trace.append(trace_line(f"OpenAI web-search browse call succeeded (tool='{tool_type}')"))
            return getattr(response, "output_text", "") or "", trace
        except Exception as exc:
            trace.append(trace_line(f"OpenAI web-search browse call failed (tool='{tool_type}'): {exc}"))
    return "", trace


async def _extract(
    client, findings_text: str, niche: str, channel: str, query: str, discovery_pass: int
) -> list[RawCandidate]:
    resp = await client.chat.completions.create(
        model=EXTRACTION_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_INSTRUCTIONS},
            {"role": "user", "content": findings_text},
        ],
    )
    payload = json.loads(resp.choices[0].message.content or "{}")
    raw_items = payload.get("candidates", [])

    candidates = []
    for item in raw_items:
        source_url = item.get("source_url") or ""
        if not source_url or not item.get("founder_name") or not item.get("startup_name"):
            continue
        co_founders = [n for n in (item.get("co_founders") or []) if n and n != item["founder_name"]]
        candidates.append(
            RawCandidate(
                founder_name=item["founder_name"],
                co_founders=co_founders,
                founder_city=item.get("city"),
                founder_country=item.get("country"),
                startup_name=item["startup_name"],
                website=item.get("website"),
                estimated_founded_year=item.get("founded_year"),
                niche=niche,
                one_line_description=item.get("one_line_description", ""),
                product_stage=item.get("product_stage") or "unknown",
                team_size_estimate=item.get("team_size_estimate"),
                tech_stack_signals=item.get("tech_stack") or [],
                has_clients=item.get("has_clients"),
                funding_status=item.get("funding_status") or "unknown",
                source_channel=_CHANNEL_LABELS.get(channel, channel),
                search_queries_used=[query],
                discovery_signals=item.get("discovery_signals") or [],
                discovery_pass=discovery_pass,
                evidence=[
                    EvidenceItem(
                        source_url=source_url,
                        snippet=(item.get("snippet") or "")[:200],
                        date_captured=today_iso(),
                    )
                ],
                date_found=today_iso(),
            )
        )
    return candidates
