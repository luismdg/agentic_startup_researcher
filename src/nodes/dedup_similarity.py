"""Node 6 — Dedup / Already-Mapped Similarity Node (Section 6a). Scoped
narrowly to "have we already found this startup before?" — never enriches a
candidate from a similar-but-different company, and never merges on a
single weak signal alone. Weighted signals, strongest to weakest: domain
match > founder name match > fuzzy startup-name match > description
similarity (corroborating only)."""

from src.models.pipeline import RawCandidate, WorkingCandidate
from src.services.data_store import load_known_startups
from src.utils.similarity import description_similarity, domain_match, fuzzy_ratio, name_match
from src.utils.tracing import trace_line

DOMAIN_WEIGHT = 0.5
NAME_WEIGHT = 0.3
FUZZY_WEIGHT = 0.15
DESC_WEIGHT = 0.05

DUPLICATE_THRESHOLD = 0.75
POSSIBLE_DUPLICATE_THRESHOLD = 0.35

_FUZZY_NAME_FLOOR = 0.8
_DESC_SIM_FLOOR = 0.3


async def dedup(candidates: list[RawCandidate], niche: str) -> tuple[list[WorkingCandidate], list[str]]:
    known = load_known_startups()
    trace: list[str] = []
    working: list[WorkingCandidate] = []

    for c in candidates:
        best_score = 0.0
        best_match: str | None = None
        best_signals: list[str] = []

        for entry in known:
            score = 0.0
            signals: list[str] = []

            if domain_match(c.website, entry.get("website")):
                score += DOMAIN_WEIGHT
                signals.append("domain match")

            if name_match(c.founder_name, entry.get("founder_name")):
                score += NAME_WEIGHT
                signals.append("founder name match")

            name_ratio = fuzzy_ratio(c.startup_name, entry.get("startup_name"))
            if name_ratio >= _FUZZY_NAME_FLOOR:
                score += FUZZY_WEIGHT * name_ratio
                signals.append(f"startup name similarity ({name_ratio:.2f})")

            desc_sim = await description_similarity(
                c.one_line_description, entry.get("one_line_description")
            )
            if desc_sim >= _DESC_SIM_FLOOR:
                score += DESC_WEIGHT * desc_sim
                signals.append(f"description similarity ({desc_sim:.2f})")

            if score > best_score:
                best_score, best_match, best_signals = score, entry.get("startup_name"), signals

        if best_score >= DUPLICATE_THRESHOLD:
            trace.append(
                trace_line(
                    f"Node 6 (dedup_similarity): '{c.startup_name}' marked duplicate of "
                    f"'{best_match}' (score {best_score:.2f}, signals: {best_signals}) — dropped"
                )
            )
            continue

        if best_score >= POSSIBLE_DUPLICATE_THRESHOLD:
            trace.append(
                trace_line(
                    f"Node 6: '{c.startup_name}' flagged possible_duplicate of '{best_match}' "
                    f"(score {best_score:.2f}, signals: {best_signals}) — continues in pipeline"
                )
            )
            working.append(
                WorkingCandidate(
                    **c.model_dump(),
                    dedup_status="possible_duplicate",
                    possible_duplicate_of=best_match,
                    dedup_signals_matched=best_signals,
                )
            )
            continue

        working.append(WorkingCandidate(**c.model_dump(), dedup_status="genuinely_new"))

    trace.append(trace_line(f"Node 6: {len(working)}/{len(candidates)} candidates continue past dedup"))
    return working, trace
