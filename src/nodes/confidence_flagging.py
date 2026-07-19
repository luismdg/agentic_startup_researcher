"""Node 9 — Confidence & Red-Flag Node. Assigns confidence from how many
independent evidence sources corroborate a candidate, and raises red flags
for internally inconsistent claims (e.g. a 9-day-old domain paired with a
claimed team of 10)."""

from datetime import date

from src.models.candidate import Candidate, Confidence, LeadStatus
from src.utils.tracing import trace_line


def flag(candidates: list[Candidate]) -> tuple[list[Candidate], list[str]]:
    trace: list[str] = []
    flagged: list[Candidate] = []

    for c in candidates:
        confidence, reasoning = _compute_confidence(c)
        red_flags = _compute_red_flags(c)
        status = _compute_status(c, confidence)
        next_step = _recommend_next_step(c, confidence)

        updated = c.model_copy(
            update={
                "confidence": confidence,
                "confidence_reasoning": reasoning,
                "red_flags": red_flags,
                "status": status,
                "recommended_next_step": next_step,
                "agent_trace": [
                    *c.agent_trace,
                    trace_line(
                        f"Node 9 (confidence_flagging): '{c.startup_name}' -> "
                        f"confidence={confidence}, red_flags={len(red_flags)}"
                    ),
                ],
            }
        )
        trace.append(trace_line(f"Node 9: '{c.startup_name}' finalized as {status}"))
        flagged.append(updated)

    return flagged, trace


def _compute_confidence(c: Candidate) -> tuple[Confidence, str]:
    evidence_count = len(c.evidence)
    if evidence_count == 0:
        return "low", "No verifiable evidence sources were captured for this candidate."

    anchors = sum(
        [
            bool(c.traction_signals.github_repo_url),
            bool(c.website),
            bool(c.founder_linkedin),
        ]
    )
    if anchors >= 2 and evidence_count >= 2:
        return "high", "Multiple independent evidence sources corroborate this candidate."
    if anchors >= 1:
        return "medium", "At least one concrete artifact confirms this candidate exists, but corroboration is limited."
    return "low", "Only a single weak signal supports this candidate; needs verification before acting."


def _compute_red_flags(c: Candidate) -> list[str]:
    flags: list[str] = []

    if c.domain_registered_date:
        try:
            days_old = (date.today() - date.fromisoformat(c.domain_registered_date)).days
            if days_old < 14 and (c.team_size_estimate or 0) > 2:
                flags.append(
                    f"Domain registered only {days_old} days ago but claims a team of "
                    f"{c.team_size_estimate} — verify maturity claims."
                )
        except ValueError:
            pass

    if c.product_stage == "launched" and not c.website:
        flags.append("Marked as launched but no live website was found.")

    if (c.funding_status == "seed" or c.investors_mentioned) and len(c.evidence) < 2:
        flags.append("Funding/investor claim is based on thin evidence — verify before treating as confirmed.")

    if c.founder_name.strip().lower().startswith("unknown"):
        flags.append("Founder identity not independently verified — sourced from raw web search only.")

    if (
        c.team_size_estimate
        and c.team_size_estimate > 5
        and not c.traction_signals.press_mentions
        and not c.traction_signals.job_postings_found
    ):
        flags.append("Claims a team size that isn't corroborated by any job postings or press.")

    return flags


def _compute_status(c: Candidate, confidence: Confidence) -> LeadStatus:
    if c.dedup_status == "possible_duplicate":
        return "needs_verification"
    if confidence == "low":
        return "needs_verification"
    return "new_lead"


def _recommend_next_step(c: Candidate, confidence: Confidence) -> str:
    if c.dedup_status == "possible_duplicate":
        return f"Resolve possible duplicate against '{c.possible_duplicate_of}' before proceeding."
    if confidence == "high":
        return "Strong cold-start candidate — worth direct outreach before it gets more visible."
    if confidence == "medium":
        return "Needs light verification (confirm team/product details) before outreach."
    return "Needs verification — evidence is thin; confirm the candidate is real before acting."
