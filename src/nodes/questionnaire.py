"""Returns which of SearchFilters' richer attributes are worth surfacing
for a given niche + stage — "one big form that adapts" rather than a fixed
kitchen-sink form or a back-and-forth chat. Reuses niche_adapter's
fallback-resolution logic so an unmatched niche still gets a sensible
questionnaire instead of an empty one. The frontend calls this once
niche (+ stage, if already picked) are chosen, to decide which fields to
show, then submits everything together to POST /search."""

from src.models.pipeline import NicheProfile
from src.nodes.niche_adapter import resolve_niche_profile

ALWAYS_SHOWN_FIELDS = ["niche", "geography", "city", "channels", "stage_signal", "keywords"]


def resolve_questionnaire(niche: str, stage_signal: str | None) -> dict:
    profile, trace = resolve_niche_profile(niche)
    return {
        "niche": profile.niche,
        "resolved_via": profile.resolved_via,
        "always_show": ALWAYS_SHOWN_FIELDS,
        "recommended_fields": _recommended_fields(profile, stage_signal),
        "suggested_keywords": profile.questionnaire.get("suggested_keywords", []),
        "trace": trace,
    }


def _recommended_fields(profile: NicheProfile, stage_signal: str | None) -> list[str]:
    q = profile.questionnaire or {}
    relevant = set(q.get("relevant_attributes", []))
    by_stage = q.get("by_stage", {})
    if stage_signal:
        relevant |= set(by_stage.get(stage_signal, []))
    return sorted(relevant)
