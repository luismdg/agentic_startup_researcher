"""Shared helpers for every src/tools/*.py module. Each tool exposes one
async `search(query, niche, discovery_pass, filters_context)` function
returning RawCandidate objects, and decides internally (via
src.config.mock_mode) whether to hit a real API, browse the live web via
src.orchestration.web_research_agent, or read from the synthetic
/data/mock-search-results.json pool."""

from datetime import date

from src.config import get_settings
from src.models.candidate import EvidenceItem, TractionSignals
from src.models.pipeline import RawCandidate
from src.services.data_store import load_mock_search_results
from src.utils.tracing import trace_line

today_iso = lambda: date.today().isoformat()  # noqa: E731


def mock_candidates_for(
    source: str, niche: str, query: str, discovery_pass: int
) -> list[RawCandidate]:
    data = load_mock_search_results()
    matches = [
        entry
        for entry in data["results"]
        if entry.get("source") == source and entry.get("niche") == niche
    ]
    return [_entry_to_raw_candidate(entry, query, discovery_pass) for entry in matches]


def mock_or_none(
    source: str, niche: str, query: str, discovery_pass: int, reason: str
) -> tuple[list[RawCandidate], list[str]]:
    """The final fallback every tool calls when it has no (more) real data
    to offer. Returns synthetic mock candidates by default — but if
    GENUINE_RESULTS_ONLY is set, it never substitutes fabricated data for a
    real search that found nothing or failed; it honestly returns empty."""
    if get_settings().genuine_only:
        return [], [trace_line(f"{reason} — GENUINE_RESULTS_ONLY is set, returning no results instead of mock data")]
    return mock_candidates_for(source, niche, query, discovery_pass), []


def _entry_to_raw_candidate(entry: dict, query: str, discovery_pass: int) -> RawCandidate:
    return RawCandidate(
        founder_name=entry["founder_name"],
        founder_city=entry.get("founder_city"),
        founder_country=entry.get("founder_country"),
        founder_linkedin=entry.get("founder_linkedin"),
        founder_education=entry.get("founder_education"),
        founder_prior_ventures=entry.get("founder_prior_ventures", []),
        startup_name=entry["startup_name"],
        website=entry.get("website"),
        domain_registered_date=entry.get("domain_registered_date"),
        estimated_founded_year=entry.get("estimated_founded_year"),
        niche=entry["niche"],
        one_line_description=entry["one_line_description"],
        product_stage=entry.get("product_stage", "unknown"),
        team_size_estimate=entry.get("team_size_estimate"),
        tech_stack_signals=entry.get("tech_stack_signals", []),
        has_clients=entry.get("has_clients"),
        traction_signals=TractionSignals(**entry.get("traction_signals", {})),
        funding_status=entry.get("funding_status", "unknown"),
        funding_amount_estimate=entry.get("funding_amount_estimate"),
        investors_mentioned=entry.get("investors_mentioned", []),
        source_channel=entry["source_channel"],
        search_queries_used=[query],
        discovery_signals=entry.get("discovery_signals", []),
        discovery_pass=discovery_pass,
        evidence=[EvidenceItem(**e) for e in entry.get("evidence", [])],
        trace=[
            trace_line(
                f"[mock] matched synthetic candidate '{entry['startup_name']}' "
                f"for query '{query}'"
            )
        ],
        date_found=entry["date_found"],
    )
