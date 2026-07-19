"""
Runs the memo generator prompt and assembles the full InvestmentMemo.

axis_scores and thesis_fit are passed in already computed (see
scorer_service.py / thesis_engine.py) and just attached here -- the memo LLM
call never re-derives them, so the numbers on the dashboard and the numbers
referenced in the memo narrative can never disagree with each other.

trust_summary is a plain tally over the claims the LLM actually produced,
computed in Python for the same reason the 3 axes aren't averaged: a
distribution the reader can recompute by hand is trustworthy, a single
LLM-asserted "trust score" would just be a black box one level down.

_sanitize_claims does more than drop hallucinated evidence ids -- it also
re-checks "verified" against the confidence rubric memo_prompts.py itself
states (2+ independent sources, or one "primary"-reliability source).
Observed in practice: a model labeled a claim "verified" off a single
"secondary" (Crunchbase) snippet, which the rubric it was given does not
allow. Checking evidence *ids* were real wasn't enough -- the confidence
*label* also needs to be earned by the evidence's own reliability tag, or
the Trust Score is only as honest as the model's self-assessment, i.e.
exactly the black box this whole mechanism exists to avoid.

_deduplicate_claim_ids exists because of a live bug, not a hypothetical one:
observed in production (frontend_vcBrain, React duplicate-key warnings) that
the model writes each section's claims independently, with no view of ids
it already used in other sections of the SAME memo -- so short, generic ids
like "c1"/"c2" routinely collide across company_snapshot vs swot vs
traction_kpis. Per-section validation (which is all _sanitize_claims does)
can't catch this; it has to run on the fully-assembled claim list.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List

from app.models import (
    AxisScoreSet,
    BeachheadMarketAnalysis,
    BusinessSegmentCandidate,
    BusinessSegmentEvaluation,
    CompanyRecord,
    EndUserProfile,
    EvidenceSnippet,
    ExtendedAnalysisDraft,
    InvestmentMemo,
    MemoDraft,
    ThesisConfig,
    ThesisFitResult,
    TrustedClaim,
    TrustSummary,
)
from app.prompts.extended_analysis_prompts import build_extended_analysis_messages
from app.prompts.memo_prompts import build_memo_messages
from app.services.llm_client import call_structured


def _all_claims(draft: MemoDraft) -> List[TrustedClaim]:
    claims: List[TrustedClaim] = []
    for section in (draft.company_snapshot, draft.investment_hypotheses, draft.problem_product, draft.traction_kpis):
        claims.extend(section.claims)
    for bucket in (draft.swot.strengths, draft.swot.weaknesses, draft.swot.opportunities, draft.swot.threats):
        claims.extend(bucket)
    return claims


def _deduplicate_claim_ids(claims: List[TrustedClaim]) -> None:
    seen: set[str] = set()
    for claim in claims:
        original_id = claim.claim_id
        candidate = original_id
        suffix = 2
        while candidate in seen:
            candidate = f"{original_id}_{suffix}"
            suffix += 1
        claim.claim_id = candidate
        seen.add(candidate)


def _sanitize_claims(claims: List[TrustedClaim], evidence_by_id: Dict[str, EvidenceSnippet]) -> None:
    for claim in claims:
        bad_ids = [i for i in claim.evidence_ids if i not in evidence_by_id]
        if bad_ids:
            claim.evidence_ids = [i for i in claim.evidence_ids if i in evidence_by_id]
            claim.reasoning += f" [sanitized: model cited unknown evidence id(s) {bad_ids}, dropped]"

        if not claim.evidence_ids:
            if claim.confidence_level != "unverifiable":
                claim.confidence_level = "unverifiable"
                claim.reasoning += " [sanitized: no valid evidence id remained, downgraded to unverifiable]"
            continue

        if claim.confidence_level == "verified":
            reliabilities = [evidence_by_id[i].reliability for i in claim.evidence_ids]
            has_primary_source = "primary" in reliabilities
            is_corroborated = len(claim.evidence_ids) >= 2
            if not (has_primary_source or is_corroborated):
                claim.confidence_level = "likely"
                claim.reasoning += (
                    " [sanitized: downgraded from 'verified' to 'likely' -- rubric requires 2+ "
                    "independent sources or one 'primary' source; this claim has neither]"
                )


def generate_memo(
    company: CompanyRecord,
    thesis: ThesisConfig,
    axis_scores: AxisScoreSet,
    thesis_fit: ThesisFitResult,
) -> InvestmentMemo:
    messages = build_memo_messages(company, thesis, axis_scores, thesis_fit)
    draft = call_structured(messages, MemoDraft)

    evidence_by_id = {ev.id: ev for ev in company.evidence_pool}
    claims = _all_claims(draft)
    _deduplicate_claim_ids(claims)
    _sanitize_claims(claims, evidence_by_id)

    counts = Counter(c.confidence_level for c in claims)
    trust_summary = TrustSummary(
        total_claims=len(claims),
        verified=counts.get("verified", 0),
        likely=counts.get("likely", 0),
        uncertain=counts.get("uncertain", 0),
        unverifiable=counts.get("unverifiable", 0),
    )

    return InvestmentMemo(
        company_id=company.id,
        thesis_id=thesis.id,
        generated_at=datetime.now(timezone.utc),
        company_snapshot=draft.company_snapshot,
        investment_hypotheses=draft.investment_hypotheses,
        swot=draft.swot,
        problem_product=draft.problem_product,
        traction_kpis=draft.traction_kpis,
        axis_scores=axis_scores,
        thesis_fit=thesis_fit,
        trust_summary=trust_summary,
    )


def generate_extended_analysis(
    company: CompanyRecord,
    thesis: ThesisConfig,
    axis_scores: AxisScoreSet,
) -> tuple[EndUserProfile, BeachheadMarketAnalysis, BusinessSegmentEvaluation]:
    """
    Optional, opt-in: End User Profile + Beachhead Market Analysis + a
    10-criterion Business Segment scoring table. Costs one extra LLM call --
    callers (main.py) should only invoke this when explicitly requested, not
    as part of the default memo flow, so nobody pays for it unless they ask.

    total_score and recommended_segment are computed here in Python, never
    asked of the model -- same reasoning as everywhere else in this file:
    a ranking is arithmetic, not the model's opinion relabeled as a ranking.
    """
    messages = build_extended_analysis_messages(company, thesis, axis_scores)
    draft = call_structured(messages, ExtendedAnalysisDraft)

    evidence_by_id = {ev.id: ev for ev in company.evidence_pool}
    # Deduplicated together, not separately -- both claim lists render side
    # by side in the extended-analysis view, so their ids share one
    # namespace the same way the core memo's sections do.
    _deduplicate_claim_ids(draft.end_user_profile.claims + draft.market_analysis.claims)
    _sanitize_claims(draft.end_user_profile.claims, evidence_by_id)
    _sanitize_claims(draft.market_analysis.claims, evidence_by_id)

    scored_segments = [
        BusinessSegmentCandidate(
            segment_name=seg.segment_name,
            description=seg.description,
            criteria=seg.criteria,
            total_score=sum(c.score for c in seg.criteria),
            flags=seg.flags,
        )
        for seg in draft.segment_evaluation.segments
    ]
    scored_segments.sort(key=lambda s: s.total_score, reverse=True)
    recommended_segment = scored_segments[0].segment_name if scored_segments else ""

    segment_evaluation = BusinessSegmentEvaluation(
        segments=scored_segments,
        recommended_segment=recommended_segment,
    )

    return draft.end_user_profile, draft.market_analysis, segment_evaluation
