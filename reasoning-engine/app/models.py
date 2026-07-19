"""
Data structures for the Reasoning & Experience layer.

Layering, upstream to downstream:

  EvidenceSnippet / CompanyRecord   <- owned by teammate (Memory/Sourcing layer).
                                       Defined here only as a MOCK of their schema
                                       so we aren't blocked. Swap mock_data.py for
                                       their real output later; nothing else changes
                                       as long as field names line up.
  ThesisConfig                      <- investor's configurable lens. Never hardcode
                                       a fund's preferences anywhere else; every
                                       scoring/filtering call takes this as input.
  ThesisFitResult                   <- deterministic hard-filter + soft-fit result,
                                       computed in Python, NOT by the LLM.
  AxisScore / AxisScoreSet          <- the 3 independent scores (Founder, Market,
                                       Idea-vs-Market). Deliberately NOT averaged.
  TrustedClaim                      <- one factual assertion + its confidence +
                                       its evidence pointer. Granularity is the
                                       CLAIM, not the company or the memo.
  InvestmentMemo                    <- assembled from the above. Every section is
                                       either grounded in evidence or explicitly
                                       flagged as a gap.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Upstream schema (mocked stand-in for teammate's Memory/Sourcing output)
# ---------------------------------------------------------------------------

class EvidenceSnippet(BaseModel):
    id: str
    source: str  # e.g. "Pitch deck p.12", "LinkedIn", "TechCrunch", "Founder call transcript"
    source_url: Optional[str] = None
    snippet_text: str
    retrieved_at: datetime
    reliability: Literal["primary", "secondary", "self_reported", "inferred"]
    # primary        = verifiable external record (filing, press release, verified data-room doc)
    # secondary       = third-party reporting/aggregator (TechCrunch, Crunchbase estimate)
    # self_reported   = founder/deck/pitch claim, uncorroborated
    # inferred        = derived by the sourcing pipeline (e.g. NLP-extracted from a call transcript)


class FounderRecord(BaseModel):
    id: str
    name: str
    role: str
    linkedin_url: Optional[str] = None
    background_summary: Optional[str] = None
    prior_exits: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)


class CompanyRecord(BaseModel):
    id: str
    name: str
    one_liner: str
    sector: str
    sub_sector: Optional[str] = None
    # Optional: some upstream sources (e.g. raw sourcing/discovery output) only
    # know product maturity ("mvp", "launched"), not a confirmed funding round.
    # None means "round genuinely unknown" -- never guessed from product stage
    # or team size. thesis_engine treats None as a hard-filter failure with an
    # explicit "stage unknown" note, not a silent pass or a guessed match.
    stage: Optional[Literal["pre_seed", "seed", "series_a", "series_b", "series_c_plus"]] = None
    # Optional for the same reason stage is: the real sourcing service can
    # return founder_country=null (e.g. a Reddit/Twitter lead with no
    # disclosed location). None means genuinely unknown, not "unspecified
    # but assume domestic" -- thesis_engine treats it as an explicit
    # hard-filter failure, same pattern as stage.
    geography: Optional[str] = None
    founded_date: Optional[date] = None
    founders: List[FounderRecord] = Field(default_factory=list)

    funding_raised_usd: Optional[float] = None
    last_round_valuation_usd: Optional[float] = None
    revenue_arr_usd: Optional[float] = None
    traction_metrics: Dict[str, float] = Field(default_factory=dict)  # e.g. {"mau": 12000, "mom_growth": 0.18}

    market_description: Optional[str] = None
    tam_estimate_usd: Optional[float] = None
    competitors: List[str] = Field(default_factory=list)

    cap_table_disclosed: bool = False
    cap_table: Optional[Dict[str, float]] = None  # None/absent -> memo must say "not disclosed"

    # Handed off by teammate's cold-start tiering; used as an input signal, not
    # a replacement for our own Founder axis score.
    founder_score: Optional[float] = None
    cold_start_tier: Optional[Literal["tier_1_verified", "tier_2_partial", "tier_3_cold"]] = None

    evidence_pool: List[EvidenceSnippet] = Field(default_factory=list)
    last_updated: datetime


# ---------------------------------------------------------------------------
# Raw upstream schema: Agentic Sourcing Search ("Discover" scan)
#
# This is the *raw* per-lead output of the teammate's sourcing agent -- one
# step further upstream than CompanyRecord. It is NOT consumed by the
# scorer/memo/thesis engine directly; app/services/sourcing_adapter.py maps
# it into a CompanyRecord + EvidenceSnippet list, once, so nothing downstream
# has to know this schema exists. Keeping it as its own set of models (rather
# than trying to make CompanyRecord fit both shapes) keeps the "one company
# schema, one contract" property intact even as upstream sourcing evolves.
#
# Reconciled 2026-07-19 against the actual running sourcing service
# (agentic_startup_researcher/src/models/candidate.py), not just its docs.
# Real differences from the earlier doc-only version of this schema:
#   - added: co_founders, has_clients, discovery_pass, dedup_status,
#     possible_duplicate_of, dedup_signals_matched, discovery_value_score,
#     discovery_value_reasoning
#   - removed: similar_competitors_found (does not exist in the real
#     Candidate model at all -- CompanyRecord.competitors is left empty by
#     the adapter now, see sourcing_adapter.py)
#   - most fields the real model defaults (product_stage, funding_status,
#     confidence, status, etc.) are made Optional-with-default here too,
#     since the real service does return partially-defaulted records.
# ---------------------------------------------------------------------------

class SourcingTractionSignals(BaseModel):
    github_repo_url: Optional[str] = None
    github_commit_activity: Optional[str] = None
    linkedin_followers: Optional[int] = None
    twitter_followers: Optional[int] = None
    press_mentions: List[str] = Field(default_factory=list)
    job_postings_found: List[str] = Field(default_factory=list)


class SourcingEvidenceItem(BaseModel):
    source_url: str
    snippet: str
    date_captured: date


class SourcingResult(BaseModel):
    founder_name: str
    co_founders: List[str] = Field(default_factory=list)  # never merged into founder_name upstream
    founder_city: Optional[str] = None
    founder_country: Optional[str] = None
    founder_linkedin: Optional[str] = None
    founder_education: Optional[str] = None
    founder_prior_ventures: List[str] = Field(default_factory=list)

    startup_name: str
    website: Optional[str] = None
    domain_registered_date: Optional[date] = None
    estimated_founded_year: Optional[int] = None

    niche: str
    one_line_description: str
    product_stage: Literal["idea", "mvp", "launched", "unknown"] = "unknown"
    team_size_estimate: Optional[int] = None
    tech_stack_signals: List[str] = Field(default_factory=list)
    has_clients: Optional[bool] = None

    traction_signals: SourcingTractionSignals = Field(default_factory=SourcingTractionSignals)

    funding_status: Literal["bootstrapped", "pre-seed", "seed", "unknown"] = "unknown"
    funding_amount_estimate: Optional[str] = None
    investors_mentioned: List[str] = Field(default_factory=list)

    source_channel: str
    search_queries_used: List[str] = Field(default_factory=list)
    discovery_signals: List[str] = Field(default_factory=list)
    discovery_pass: int = 1

    # Node 6 (dedup) output. A "possible_duplicate" still gets scored/memoed
    # like any other candidate -- only an exact "duplicate" match is dropped
    # by the sourcing service itself before this ever reaches the adapter.
    dedup_status: Literal["genuinely_new", "possible_duplicate"] = "genuinely_new"
    possible_duplicate_of: Optional[str] = None
    dedup_signals_matched: List[str] = Field(default_factory=list)

    # Node 7 (discovery scoring) output -- how hard-to-find/low-visibility
    # this candidate is, NOT an investment judgment. Distinct from, and never
    # substituted for, CompanyRecord.founder_score / our own axis scores.
    discovery_value_score: float = 0.0
    discovery_value_reasoning: str = ""

    confidence: Literal["low", "medium", "high"] = "low"
    confidence_reasoning: str = ""
    evidence: List[SourcingEvidenceItem] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    agent_trace: List[str] = Field(default_factory=list)
    recommended_next_step: str = ""
    date_found: date
    status: Literal["new_lead", "needs_verification", "activated"] = "new_lead"


class SourcingQuery(BaseModel):
    niche: str
    run_date: date
    passes_executed: int = 1
    founder_view: bool = False


class SourcingSearchResponse(BaseModel):
    query: SourcingQuery
    results: List[SourcingResult]


# ---------------------------------------------------------------------------
# Thesis Engine
# ---------------------------------------------------------------------------

class ThesisConfig(BaseModel):
    id: str
    investor_name: str
    sectors: List[str]
    stages: List[Literal["pre_seed", "seed", "series_a", "series_b", "series_c_plus"]]
    geographies: List[str]
    check_size_min_usd: float
    check_size_max_usd: float
    target_ownership_pct: float  # e.g. 0.10 for 10%
    risk_appetite: Literal["conservative", "balanced", "aggressive"]
    notes: Optional[str] = None  # freeform investor guidance injected into prompts


class ThesisFitResult(BaseModel):
    passes_hard_filters: bool
    hard_filter_failures: List[str] = Field(default_factory=list)
    ownership_feasibility: Literal["likely", "stretch", "unlikely", "unknown"]
    ownership_note: str
    risk_alignment_note: str  # short note on how risk_appetite reads on this specific opportunity


# ---------------------------------------------------------------------------
# 3-axis scoring
# ---------------------------------------------------------------------------

AxisName = Literal["founder", "market", "idea_market_fit"]
Trend = Literal["improving", "declining", "stable"]
Confidence = Literal["high", "medium", "low"]


class AxisScore(BaseModel):
    # Field order matters: reasoning fields are declared BEFORE the numeric
    # verdict so a structured-output model is nudged to "think" before it
    # commits to a score, rather than picking a number and rationalizing it.
    axis: AxisName
    key_factors: List[str]
    supporting_evidence_ids: List[str]
    justification: str
    flags: List[str] = Field(default_factory=list)  # e.g. ["no corroboration on prior exit claim"]
    confidence: Confidence  # confidence in the score GIVEN available evidence, separate from the score itself
    trend: Trend
    score: int = Field(ge=1, le=10)


class AxisScoreSet(BaseModel):
    company_id: str
    thesis_id: str
    generated_at: datetime
    founder: AxisScore
    market: AxisScore
    idea_market_fit: AxisScore

    def as_list(self) -> List[AxisScore]:
        return [self.founder, self.market, self.idea_market_fit]


class AxisScoreSetDraft(BaseModel):
    """
    Exactly what the scorer LLM call returns. Same reasoning as MemoDraft:
    company_id/thesis_id/generated_at are provenance the service layer
    already knows, not something the model should be trusted to fill in.
    """
    founder: AxisScore
    market: AxisScore
    idea_market_fit: AxisScore


# ---------------------------------------------------------------------------
# Trust Score (per claim, not per company)
# ---------------------------------------------------------------------------

ClaimConfidence = Literal["verified", "likely", "uncertain", "unverifiable"]
# verified      = corroborated by >=2 independent sources, or 1 "primary" source
# likely        = single "secondary" source, or a direct reasonable inference from primary data
# uncertain     = "self_reported" only, no corroboration
# unverifiable  = no evidence snippet supports it at all (should be rare; prefer a data_gap instead)


class TrustedClaim(BaseModel):
    claim_id: str
    claim_text: str
    confidence_level: ClaimConfidence
    evidence_ids: List[str] = Field(default_factory=list)
    reasoning: str  # one line: why this confidence level


class MemoSection(BaseModel):
    title: str
    content: str  # narrative, may reference claim_ids inline like "...grew 3x in 6 months [c3]"
    claims: List[TrustedClaim] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)  # e.g. "Cap table: not disclosed"


class ProblemProductSection(BaseModel):
    """
    Two genuinely distinct fields, not one narrative split in two. This used
    to be a single MemoSection.content covering both -- found (via a live
    render, not just a schema review) that any consumer expecting to compose
    "the problem, then how the product solves it" as two different strings
    (frontend_vcBrain's snapshotNarrative.ts does exactly this) would render
    the same paragraph twice back to back. Asking the model for both
    separately, once, is the actual fix -- not deduplicating downstream.
    """
    problem: str
    product: str
    claims: List[TrustedClaim] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)


class SWOTSection(BaseModel):
    strengths: List[TrustedClaim] = Field(default_factory=list)
    weaknesses: List[TrustedClaim] = Field(default_factory=list)
    opportunities: List[TrustedClaim] = Field(default_factory=list)
    threats: List[TrustedClaim] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Extended analysis (optional, opt-in): End User Profile, Beachhead Market,
# Business Segment scoring. NOT part of the 5 required memo sections -- these
# cost a separate LLM call and are only generated when explicitly requested
# (see generate_extended_analysis in memo_service.py), so the default memo
# flow's cost and behavior are unchanged for anyone who doesn't ask for this.
# ---------------------------------------------------------------------------

class EndUserProfile(BaseModel):
    """
    The target end user's persona for the company being evaluated -- NOT a
    fact CompanyRecord carries directly, so this is analyst synthesis over
    whatever evidence exists (market_description, evidence_pool). Each field
    is independently optional: prefer an honest data_gap over a plausible-
    sounding invented persona detail, same rule as the rest of the memo.
    """
    demographics: Optional[str] = None
    psychographics: Optional[str] = None
    proxy_products: List[str] = Field(default_factory=list)  # products this persona already uses/buys
    watering_holes: List[str] = Field(default_factory=list)  # where to find/reach this persona
    day_in_the_life: Optional[str] = None
    priorities: List[str] = Field(default_factory=list)
    claims: List[TrustedClaim] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)


class BeachheadMarketAnalysis(BaseModel):
    """
    TAM/SAM/SOM and CAGR here are almost never directly stated in a source
    snippet -- they're usually derived. Each is still routed through
    TrustedClaim so the derivation and confidence are visible rather than
    presented as a bare number, same principle as everywhere else in the
    memo: an estimate is fine, a black-box estimate is not.
    """
    primary_end_user: Optional[str] = None
    economic_buyer: Optional[str] = None
    niche_cagr_pct: Optional[float] = None
    tam_usd: Optional[float] = None
    sam_usd: Optional[float] = None
    som_usd: Optional[float] = None
    narrative: str
    claims: List[TrustedClaim] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)


SegmentCriterion = Literal[
    "market_size",
    "willingness_to_pay",
    "urgency_pain_severity",
    "product_fit",
    "data_availability",
    "sales_channel_efficiency",
    "integration_complexity",
    "competitive_intensity",
    "regulatory_risk",
    "expansion_potential",
]

SEGMENT_CRITERION_LABELS: Dict[str, str] = {
    "market_size": "Market size / reachable customers",
    "willingness_to_pay": "Budget / willingness to pay for AI + workflow tools",
    "urgency_pain_severity": "Urgency / pain severity (cost, cycle time, throughput)",
    "product_fit": "Fit with product capabilities",
    "data_availability": "Data availability & quality to train/operate well",
    "sales_channel_efficiency": "Sales channel + acquisition efficiency",
    "integration_complexity": "Integration / implementation complexity",
    "competitive_intensity": "Competitive intensity & differentiation potential",
    "regulatory_risk": "Regulatory / risk surface (liability, confidentiality, ethics)",
    "expansion_potential": "Long-term expansion potential (within account + cross-sell)",
}

_EXPECTED_SEGMENT_CRITERIA = frozenset(SEGMENT_CRITERION_LABELS.keys())


class SegmentCriterionScore(BaseModel):
    criterion: SegmentCriterion
    # 1-5, ALWAYS oriented so 5 = most favorable for pursuing this segment --
    # including for risk-flavored criteria (regulatory_risk=5 means LOW
    # risk, not high). This is what makes total_score summable/comparable
    # across segments instead of needing per-criterion sign-flipping.
    score: int = Field(ge=1, le=5)
    justification: str  # one line


class BusinessSegmentCandidateDraft(BaseModel):
    segment_name: str
    description: str
    criteria: List[SegmentCriterionScore]
    flags: List[str] = Field(default_factory=list)

    @field_validator("criteria")
    @classmethod
    def _exactly_the_ten_expected_criteria(cls, v: List[SegmentCriterionScore]) -> List[SegmentCriterionScore]:
        seen = [c.criterion for c in v]
        if len(seen) != len(_EXPECTED_SEGMENT_CRITERIA) or set(seen) != _EXPECTED_SEGMENT_CRITERIA:
            raise ValueError(
                f"criteria must cover exactly the {len(_EXPECTED_SEGMENT_CRITERIA)} expected "
                f"keys once each: {sorted(_EXPECTED_SEGMENT_CRITERIA)}; got {seen}"
            )
        return v


class BusinessSegmentCandidate(BaseModel):
    segment_name: str
    description: str
    criteria: List[SegmentCriterionScore]
    total_score: int  # = sum(criteria scores), computed in Python -- see memo_service.py
    flags: List[str] = Field(default_factory=list)


class BusinessSegmentEvaluationDraft(BaseModel):
    """Exactly what the LLM returns: candidate segments and their per-criterion
    scores. total_score and recommended_segment are NOT asked of the model --
    both are arithmetic (a sum, and an argmax over that sum), computed in
    Python so the "recommended" segment is never just the model's opinion
    dressed up as a ranking."""
    segments: List[BusinessSegmentCandidateDraft]


class BusinessSegmentEvaluation(BaseModel):
    segments: List[BusinessSegmentCandidate]  # sorted best-first by total_score
    recommended_segment: str  # segments[0].segment_name


class ExtendedAnalysisDraft(BaseModel):
    """Exactly what the extended-analysis LLM call returns in one shot."""
    end_user_profile: EndUserProfile
    market_analysis: BeachheadMarketAnalysis
    segment_evaluation: BusinessSegmentEvaluationDraft


class TrustSummary(BaseModel):
    total_claims: int
    verified: int
    likely: int
    uncertain: int
    unverifiable: int
    # Deliberately NOT a single "trust score" number for the company -- that
    # would be the same averaging mistake as the 3-axis rule, one level down.
    # A distribution is honest; a single score is a black box.


class InvestmentMemo(BaseModel):
    company_id: str
    thesis_id: str
    generated_at: datetime

    company_snapshot: MemoSection
    investment_hypotheses: MemoSection
    swot: SWOTSection
    problem_product: ProblemProductSection
    traction_kpis: MemoSection

    axis_scores: AxisScoreSet
    thesis_fit: ThesisFitResult
    trust_summary: TrustSummary

    # Optional, opt-in extended analysis (see memo_service.generate_extended_analysis).
    # None until explicitly requested -- absence here just means "not asked for
    # yet", not "not available", so callers should not treat None as a data gap.
    end_user_profile: Optional[EndUserProfile] = None
    market_analysis: Optional[BeachheadMarketAnalysis] = None
    segment_evaluation: Optional[BusinessSegmentEvaluation] = None


class MemoDraft(BaseModel):
    """
    Exactly what the memo-generator LLM call returns. Deliberately narrower
    than InvestmentMemo: axis_scores, thesis_fit, and trust_summary are NOT
    asked of the LLM. axis_scores/thesis_fit are computed elsewhere (single
    source of truth, so the memo narrative can't contradict the scores shown
    on the dashboard) and trust_summary is a plain tally over the claims the
    LLM did produce, computed in Python.
    """
    company_snapshot: MemoSection
    investment_hypotheses: MemoSection
    swot: SWOTSection
    problem_product: ProblemProductSection
    traction_kpis: MemoSection


class RankedOpportunity(BaseModel):
    """Row shape for the dashboard list view."""
    company_id: str
    company_name: str
    one_liner: str
    sector: str
    stage: str
    thesis_fit: ThesisFitResult
    axis_scores: Optional[AxisScoreSet] = None  # None until scored (lazy)
    cold_start_tier: Optional[str] = None
