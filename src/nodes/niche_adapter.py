"""Node 2 — Niche Adapter. Looks up how this specific niche should be
searched (Section 7's "Akinator logic lives on the backend" requirement).
Exact match wins; otherwise the niche is matched to the nearest known niche
— preferring substring containment (e.g. "LegalTech" is literally inside
"Mexican LegalTech") over raw edit-distance ratio, since plain fuzzy
matching can pick an unrelated same-length niche instead (e.g. "LegalTech"
scores CLOSER to "Healthtech" than to "Mexican LegalTech" under
difflib.SequenceMatcher — 0.74 vs 0.69 — purely because they're similar
length and share letters, which is exactly the wrong answer). The matched
niche is then resolved to *its parent category* if it declares one
(reproducing the spec's own example: "Mexican legaltech" -> falls back to
"LatAm B2B SaaS"); if nothing matches at all, a generic profile covering
every source is used so the pipeline never runs with an empty profile."""

from difflib import get_close_matches

from src.models.pipeline import NicheProfile
from src.services.data_store import load_niche_profiles
from src.utils.tracing import trace_line

_GENERIC_DEFAULT = {
    "prioritized_sources": ["google", "github", "linkedin", "arxiv", "producthunt", "accelerators"],
    "query_templates": ["{niche} startup founder early stage"],
    "high_weight_signals": [],
    "evidence_floor": "at least one live site OR one verifiable founder profile",
    "fallback_parent_niche": None,
    "secondary_niches": [],
    "questionnaire": {
        "relevant_attributes": ["city", "business_model", "target_customer"],
        "by_stage": {
            "Idea": ["business_model", "target_customer"],
            "MVP": ["has_clients", "team_size_min", "team_size_max", "tech_stack"],
            "Launched": ["has_clients", "funding_stage_filter", "founded_after"],
            "Unknown": ["keywords"],
        },
        "suggested_keywords": [],
    },
}


def resolve_niche_profile(niche: str) -> tuple[NicheProfile, list[str]]:
    profiles = load_niche_profiles()
    trace: list[str] = []

    if niche in profiles:
        trace.append(trace_line(f"Node 2 (niche_adapter): exact profile match for '{niche}'"))
        return NicheProfile(niche=niche, resolved_via="exact", **profiles[niche]), trace

    lower_map = {key.casefold(): key for key in profiles}
    niche_lower = niche.casefold().strip()

    matched_key = _substring_match(niche_lower, lower_map)
    match_kind = "substring"
    if not matched_key:
        nearest = get_close_matches(niche_lower, lower_map.keys(), n=1, cutoff=0.5)
        matched_key = lower_map[nearest[0]] if nearest else None
        match_kind = "fuzzy"

    if matched_key:
        matched_profile = profiles[matched_key]
        parent_key = matched_profile.get("fallback_parent_niche")

        # Only escalate to the broader parent category when the match itself
        # was uncertain (fuzzy ratio). A substring match is high-confidence —
        # "LegalTech" containing-in "Mexican LegalTech" IS the answer, not a
        # cue to broaden away from it and lose its niche-specific vocabulary.
        if match_kind == "fuzzy" and parent_key and parent_key in profiles:
            trace.append(
                trace_line(
                    f"Node 2: '{niche}' matched nearest known niche '{matched_key}' ({match_kind}), "
                    f"falling back to its parent category profile '{parent_key}'"
                )
            )
            return (
                NicheProfile(niche=parent_key, resolved_via=f"fallback:{parent_key}", **profiles[parent_key]),
                trace,
            )

        trace.append(
            trace_line(f"Node 2: '{niche}' matched nearest known niche '{matched_key}' ({match_kind}) directly")
        )
        return (
            NicheProfile(niche=matched_key, resolved_via=f"fallback:{matched_key}", **matched_profile),
            trace,
        )

    trace.append(trace_line(f"Node 2: no known niche resembles '{niche}' — using generic default profile"))
    templates = [t.format(niche=niche) for t in _GENERIC_DEFAULT["query_templates"]]
    generic = {**_GENERIC_DEFAULT, "query_templates": templates}
    return NicheProfile(niche=niche, resolved_via="generic_default", **generic), trace


def _substring_match(niche_lower: str, lower_map: dict[str, str]) -> str | None:
    """Prefer a niche that literally contains (or is contained by) the
    query over anything found by fuzzy ratio — e.g. "LegalTech" should
    unambiguously match "Mexican LegalTech", not drift to an unrelated
    same-length niche like "Healthtech". Among multiple substring matches,
    prefer the closest in length (most specific)."""
    candidates = [
        original
        for lower, original in lower_map.items()
        if niche_lower in lower or lower in niche_lower
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda c: abs(len(c) - len(niche_lower)))
