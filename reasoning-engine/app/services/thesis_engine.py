"""
Thesis Engine: deterministic hard-filter + soft-fit evaluation.

Deliberately NOT an LLM call. Sector/stage/geography membership and ownership
arithmetic are exact facts, not judgment calls -- running them through an LLM
would add latency, cost, and a chance of being wrong about something a
one-line comparison gets right every time. This is what "every recommendation
scored/filtered through the thesis lens, not hardcoded to one fund" means in
practice: swap the ThesisConfig passed in and every downstream call (this
function, the scorer, the memo generator) changes behavior with it.

The 3-axis scorer still receives risk_appetite directly (see
scorer_prompts.py) because *how much a gap should hurt the score* is a
judgment call, not arithmetic -- that part legitimately belongs to the LLM.

Sector matching is a substring/keyword check, not exact equality, because
CompanyRecord.sector isn't guaranteed to be drawn from a controlled
vocabulary -- e.g. sourcing_adapter.py populates it from a sourcing agent's
freeform niche description ("AI orchestration platform for Mexican law
firms"), which will never exactly equal a thesis sector like "legaltech".
A substring match is still fully deterministic and auditable (the matched
keyword is named in the failure/pass note); it just tolerates descriptive
text instead of requiring a fixed enum. Stage and geography stay exact
matches -- those genuinely are (or should be) controlled values.
"""

from __future__ import annotations

from app.models import CompanyRecord, ThesisConfig, ThesisFitResult


def _sector_matches(company_sector: str, thesis_sectors: list[str]) -> str | None:
    """Returns the matched thesis sector keyword, or None if no overlap."""
    sector_lower = company_sector.lower()
    for candidate in thesis_sectors:
        if candidate.lower() in sector_lower:
            return candidate
    return None

_RISK_NOTES = {
    "conservative": (
        "Conservative mandate: unproven traction, thin corroboration, and "
        "single-founder risk should be weighed heavily against this opportunity."
    ),
    "balanced": "Balanced mandate: evidence weighed at face value; gaps lower confidence, not the score.",
    "aggressive": (
        "Aggressive mandate: upside potential credited even where traction is still "
        "thin, as long as there is no direct evidence of a disqualifying flaw."
    ),
}


def evaluate_thesis_fit(company: CompanyRecord, thesis: ThesisConfig) -> ThesisFitResult:
    failures = []

    matched_sector = _sector_matches(company.sector, thesis.sectors)
    if matched_sector is None:
        failures.append(f"sector '{company.sector}' does not match any thesis sector {thesis.sectors}")

    if company.stage is None:
        failures.append("stage: unknown -- sourcing did not confirm a funding round, cannot verify stage fit")
    elif company.stage not in thesis.stages:
        failures.append(f"stage '{company.stage}' not in thesis stages {thesis.stages}")

    if company.geography is None:
        failures.append("geography: unknown -- sourcing did not disclose a location, cannot verify geography fit")
    elif company.geography not in thesis.geographies:
        failures.append(f"geography '{company.geography}' not in thesis geographies {thesis.geographies}")

    ownership_feasibility, ownership_note = _evaluate_ownership(company, thesis)

    return ThesisFitResult(
        passes_hard_filters=len(failures) == 0,
        hard_filter_failures=failures,
        ownership_feasibility=ownership_feasibility,
        ownership_note=ownership_note,
        risk_alignment_note=_RISK_NOTES[thesis.risk_appetite],
    )


def _evaluate_ownership(company: CompanyRecord, thesis: ThesisConfig):
    if not company.last_round_valuation_usd:
        return "unknown", "No round valuation on file; cannot estimate the check size needed for target ownership."

    implied_check = company.last_round_valuation_usd * thesis.target_ownership_pct

    if implied_check < thesis.check_size_min_usd:
        return "stretch", (
            f"Target ownership ({thesis.target_ownership_pct:.0%}) at the last valuation "
            f"(${company.last_round_valuation_usd:,.0f}) implies a check of only "
            f"${implied_check:,.0f}, below the fund's ${thesis.check_size_min_usd:,.0f} minimum -- "
            f"would require taking more ownership than targeted, or passing."
        )
    if implied_check > thesis.check_size_max_usd:
        return "unlikely", (
            f"Target ownership at the last valuation implies a check of ${implied_check:,.0f}, "
            f"above the fund's ${thesis.check_size_max_usd:,.0f} maximum."
        )
    return "likely", (
        f"Target ownership at the last valuation implies a check of ${implied_check:,.0f}, "
        f"within the fund's ${thesis.check_size_min_usd:,.0f}-${thesis.check_size_max_usd:,.0f} range."
    )
