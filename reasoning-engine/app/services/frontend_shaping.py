"""
Shapes a PipelineResult (backend-native CompanyRecord/AxisScoreSet/
InvestmentMemo) into the exact JSON shapes frontend_vcBrain's lib/types.ts
expects (Startup, Screening, TrustScoreRecord, Memo). Kept separate from
orchestrator.py on purpose: the orchestrator produces backend-native
objects and knows nothing about any particular frontend; this module is the
only place that knows frontend_vcBrain's schema, so if that schema changes,
only this file needs to change.

Real, unavoidable mismatches this module has to resolve -- documented here
rather than silently papered over:

1. Axis score SCALE differs: this backend scores 1-10 (see AxisScore in
   models.py); frontend_vcBrain's mock Screening data is on a 0-100 scale.
   Multiplied by 10 here. A real product would pick one scale everywhere;
   for this integration, the backend's scale is intentionally coarser
   (fewer distinguishable steps forces more deliberate scoring), so the
   frontend gets the wider range via a fixed multiplier, not a re-score.

2. Trend VOCABULARY differs: backend uses improving/declining/stable;
   frontend uses up/down/flat. Direct 1:1 mapping, no information lost.

3. thesisFitScore is a single number on the frontend (used for Overview's
   ranking and average-fit stat) but this backend deliberately never
   produces one overall fit number (see thesis_engine.py). The proxy
   computed here (_thesis_fit_score) is a hard gate on passes_hard_filters
   first, not an average of the 3 axes -- consistent with "one weak axis
   shouldn't be hidden by strong ones" rather than smoothing it away.

4. Several frontend Memo fields have no backend equivalent at all
   (teamHistory, technologyDefensibility, marketSizing, competition,
   dueDiligenceLog, financials, capTable, exitPerspective). These are
   marked status="unavailable_at_this_stage" -- frontend_vcBrain already
   has a designed fallback UI for exactly this MemoField pattern, so this
   is the correct honest answer, not a workaround.

5. Memo.decision (recommendation/rationale/adversarialView/portfolioFit) is
   REQUIRED by the frontend type (no MemoField wrapper) but this backend
   has no such concept. _derive_decision() computes one deterministically
   from thesis_fit + the per-axis floor (the WORST axis gates the call, not
   an average -- see its docstring) so the recommendation is mechanically
   traceable back to the same numbers already shown, never a hidden LLM
   opinion.

6. website / foundedYear / askAmount live on the raw SourcingResult, not
   CompanyRecord (CompanyRecord deliberately doesn't carry them -- see
   sourcing_adapter.py). This module takes the original SourcingResult
   alongside the PipelineResult specifically to recover them.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models import AxisScore, InvestmentMemo, SourcingResult, TrustedClaim
from app.services.orchestrator import PipelineResult

_TREND_MAP = {"improving": "up", "declining": "down", "stable": "flat"}
_CONFIDENCE_MAP = {"verified": "high", "likely": "medium", "uncertain": "low", "unverifiable": "low"}

# SourcingResult.source_channel is already a human-readable label set by the
# sourcing service itself (src/orchestration/web_research_agent.py's
# _CHANNEL_LABELS + each tool's own real-path label) -- these are the actual
# strings it produces today. Bucketed into frontend_vcBrain's stricter
# ResearchChannelType enum for filtering only; the original label is kept
# verbatim as SourcingFeedItem.channel, this map never overwrites it.
_CHANNEL_TYPE_MAP = {
    "GitHub": "github",
    "Academic papers": "research",
    "Community": "community",
    "Reddit": "community",
    "Google search": "web",
    "Product Hunt": "web",
    "YouTube": "web",
    "Twitter/X": "web",
    "Accelerators": "accelerator",
    "Manual (fallback)": "direct",  # the hardcoded plan-C candidate -- not found via any channel
}
# status is the sourcing pipeline's own lead-processing state (has this
# lead been looked at yet), a different axis from reasoning-engine's
# invest/pass/watch recommendation computed in _derive_decision below --
# deliberately not conflated here.
_STATUS_MAP = {"new_lead": "new", "needs_verification": "reviewing", "activated": "activated"}


def to_sourcing_feed_item_json(sourcing_record: SourcingResult, company_id: str) -> Dict[str, Any]:
    return {
        "id": f"feed_{company_id}",
        "track": "outbound",  # every sourcing-pipeline result is something the agent went and found
        "date": sourcing_record.date_found.isoformat(),
        "startupName": sourcing_record.startup_name,
        "founderNames": [sourcing_record.founder_name, *sourcing_record.co_founders],
        "channel": sourcing_record.source_channel,
        "channelType": _CHANNEL_TYPE_MAP.get(sourcing_record.source_channel, "web"),
        "summary": sourcing_record.one_line_description,
        "status": _STATUS_MAP[sourcing_record.status],
        "activated": sourcing_record.status == "activated",
        # No distinct "date it was activated" fact exists upstream (only
        # date_found) -- left None rather than reusing date_found and
        # implying activation happened at discovery time.
        "activatedDate": None,
        "linkedStartupId": company_id,
    }


def _axis_score_json(axis: AxisScore) -> Dict[str, Any]:
    return {
        "score": axis.score * 10,  # 1-10 backend scale -> 0-100 frontend scale, see module docstring
        "trend": _TREND_MAP[axis.trend],
        "rationale": axis.justification,
    }


def _thesis_fit_score(result: PipelineResult) -> int:
    """A single number for the frontend's ranking/average-fit stat.
    Gate-based, not averaged: a company that fails hard filters or bottoms
    out on any one axis scores low regardless of how strong the other axes
    are -- see point 3 in the module docstring."""
    if not result.thesis_fit.passes_hard_filters:
        return 15
    worst_axis = min(a.score for a in result.axis_scores.as_list())
    if worst_axis <= 3:
        return 30
    base = worst_axis * 10
    if result.thesis_fit.ownership_feasibility == "likely":
        return min(100, base + 5)
    if result.thesis_fit.ownership_feasibility in ("stretch", "unknown"):
        return base
    return max(10, base - 15)  # "unlikely"


def to_startup_json(result: PipelineResult, sourcing_record: SourcingResult) -> Dict[str, Any]:
    company = result.company
    founded_year = (
        company.founded_date.year
        if company.founded_date
        else sourcing_record.estimated_founded_year  # explicitly an estimate upstream; passed through as-is
    )
    return {
        "id": company.id,
        "name": company.name,
        "tagline": company.one_liner,
        "oneLiner": company.one_liner,
        "founderIds": [f.id for f in company.founders],
        "sector": company.sector,
        "stage": company.stage or "unknown",
        "geography": company.geography or "unknown",
        "foundedYear": founded_year or 0,  # 0 is a visible "genuinely unknown", not a guessed year
        "website": sourcing_record.website or "",
        "status": "memo",  # every orchestrated record has reached memo generation; see docstring point 6
        "askAmount": 0,  # no ask-amount field exists anywhere upstream -- not invented, left at 0
        "proposedCheckSize": 0,
        "thesisFitScore": _thesis_fit_score(result),
        "momentumTrend": "flat",  # single snapshot only, no time series available
        "momentumHistory": [],
        "lastActivityDate": company.last_updated.date().isoformat(),
        "tags": [company.sector],
    }


def to_screening_json(result: PipelineResult) -> Dict[str, Any]:
    axis = result.axis_scores
    return {
        "startupId": result.company.id,
        "founder": _axis_score_json(axis.founder),
        "market": _axis_score_json(axis.market),
        "ideaMarketFit": _axis_score_json(axis.idea_market_fit),
        "history": [],  # single snapshot only, no time series available
    }


def _claim_source_and_type(claim: TrustedClaim, evidence_by_id: Dict[str, Any]) -> tuple[str, str]:
    if not claim.evidence_ids:
        return "analyst judgment", "inferred"
    ev = evidence_by_id.get(claim.evidence_ids[0])
    if ev is None:
        return "unknown", "inferred"
    return ev.source, ev.reliability


def to_trust_score_json(result: PipelineResult) -> Dict[str, Any]:
    memo = result.memo
    evidence_by_id = {ev.id: ev for ev in result.company.evidence_pool}

    all_claims: List[TrustedClaim] = []
    for section in (memo.company_snapshot, memo.investment_hypotheses, memo.problem_product, memo.traction_kpis):
        all_claims.extend(section.claims)
    for bucket in (memo.swot.strengths, memo.swot.weaknesses, memo.swot.opportunities, memo.swot.threats):
        all_claims.extend(bucket)

    claims_json = []
    for c in all_claims:
        source, evidence_type = _claim_source_and_type(c, evidence_by_id)
        claims_json.append({
            "id": c.claim_id,
            "claim": c.claim_text,
            "source": source,
            "evidenceType": evidence_type,
            "confidence": _CONFIDENCE_MAP[c.confidence_level],
            "verifiedDate": memo.generated_at.date().isoformat(),
            "contradiction": None,  # this backend has no contradiction-detection step
        })

    return {"startupId": result.company.id, "claims": claims_json}


def _unavailable() -> Dict[str, Any]:
    return {"status": "unavailable_at_this_stage", "value": None}


def _derive_decision(result: PipelineResult) -> Dict[str, Any]:
    """Deterministic, not an LLM opinion: gated on passes_hard_filters and
    the WORST individual axis score (never an average of the three) so the
    recommendation is mechanically traceable back to numbers already shown
    elsewhere on the page. See module docstring point 5."""
    axis_list = result.axis_scores.as_list()
    worst = min(axis_list, key=lambda a: a.score)
    fit = result.thesis_fit

    if not fit.passes_hard_filters:
        recommendation = "pass"
    elif worst.score <= 3:
        recommendation = "pass"
    elif worst.score <= 5 or fit.ownership_feasibility == "unlikely":
        recommendation = "watch"
    else:
        recommendation = "invest"

    rationale = (
        f"Deterministic, not model opinion: hard filters "
        f"{'pass' if fit.passes_hard_filters else 'fail (' + '; '.join(fit.hard_filter_failures) + ')'}; "
        f"lowest individual axis is {worst.axis} at {worst.score}/10 (axes are never averaged -- "
        f"the weakest one gates the call); ownership feasibility is {fit.ownership_feasibility}."
    )

    weaknesses_and_threats = list(result.memo.swot.weaknesses) + list(result.memo.swot.threats)

    return {
        "recommendation": recommendation,
        "checkSize": 0,  # no ask-amount data upstream to size a check against, see to_startup_json
        "rationale": rationale,
        "adversarialView": {
            "counterThesis": (
                weaknesses_and_threats[0].claim_text if weaknesses_and_threats else "No specific counter-thesis identified from available evidence."
            ),
            "keyRisks": [c.claim_text for c in weaknesses_and_threats] or ["No specific risks identified from available evidence."],
            "whatWouldChangeOurMind": f"Corroborating evidence resolving the '{worst.axis}' axis's flags: {'; '.join(worst.flags) or 'none noted'}.",
        },
        "portfolioFit": {
            "overlapWith": [],
            "diversificationNote": "Not assessed -- this backend has no access to existing portfolio holdings.",
            "concentrationRisk": "medium",  # neutral placeholder; see diversificationNote, this is not a real assessment
            "fitScore": 0,
        },
        "decidedDate": None,
    }


def to_memo_json(result: PipelineResult) -> Dict[str, Any]:
    memo: InvestmentMemo = result.memo
    company = result.company

    return {
        "startupId": company.id,
        "generatedDate": memo.generated_at.date().isoformat(),
        "companySnapshot": {
            "name": company.name,
            "sector": company.sector,
            "stage": company.stage or "unknown",
            "geography": company.geography or "unknown",
            "foundedYear": company.founded_date.year if company.founded_date else 0,
            "askAmount": 0,
            "proposedCheckSize": 0,
        },
        "investmentHypotheses": [memo.investment_hypotheses.content],
        "swot": {
            "strengths": [c.claim_text for c in memo.swot.strengths],
            "weaknesses": [c.claim_text for c in memo.swot.weaknesses],
            "opportunities": [c.claim_text for c in memo.swot.opportunities],
            "threats": [c.claim_text for c in memo.swot.threats],
        },
        "problemProduct": {
            "problem": memo.problem_product.problem,
            "product": memo.problem_product.product,
        },
        # An empty list here would be a SILENT gap -- unlike every MemoField
        # section below, TractionKpi[] has no status wrapper to say "not
        # disclosed" on its own, so a company with zero traction_metrics
        # would just render as an empty section with no explanation. Make
        # the absence explicit instead, consistent with how every other
        # missing field in this memo is handled.
        "tractionKpis": (
            [
                {"label": key, "value": str(value), "asOf": company.last_updated.date().isoformat()}
                for key, value in company.traction_metrics.items()
            ]
            if company.traction_metrics
            else [{"label": "Traction data", "value": "not disclosed", "asOf": company.last_updated.date().isoformat()}]
        ),
        "teamHistory": _unavailable(),
        "technologyDefensibility": _unavailable(),
        "marketSizing": _unavailable(),
        "competition": _unavailable(),
        "dueDiligenceLog": _unavailable(),
        "financials": _unavailable(),
        "capTable": _unavailable(),
        "exitPerspective": _unavailable(),
        "decision": _derive_decision(result),
    }
