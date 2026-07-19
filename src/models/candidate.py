from typing import Literal

from pydantic import BaseModel

ProductStage = Literal["idea", "mvp", "launched", "unknown"]
FundingStatus = Literal["bootstrapped", "pre-seed", "seed", "unknown"]
DedupStatus = Literal["genuinely_new", "possible_duplicate"]
Confidence = Literal["low", "medium", "high"]
LeadStatus = Literal["new_lead", "needs_verification", "activated"]


class TractionSignals(BaseModel):
    github_repo_url: str | None = None
    github_commit_activity: str | None = None
    linkedin_followers: int | None = None
    twitter_followers: int | None = None
    press_mentions: list[str] = []
    job_postings_found: list[str] = []


class EvidenceItem(BaseModel):
    source_url: str
    snippet: str
    date_captured: str


class Candidate(BaseModel):
    """Matches the Section 8 result schema exactly."""

    # Identity
    founder_name: str  # the primary founder for this row (see RunMeta.founder_view)
    co_founders: list[str] = []  # any other named founders — never mashed into founder_name
    founder_city: str | None = None
    founder_country: str | None = None
    founder_linkedin: str | None = None
    founder_education: str | None = None
    founder_prior_ventures: list[str] = []
    startup_name: str
    website: str | None = None
    domain_registered_date: str | None = None
    estimated_founded_year: int | None = None

    # Product & stage
    niche: str
    one_line_description: str
    product_stage: ProductStage = "unknown"
    team_size_estimate: int | None = None
    tech_stack_signals: list[str] = []
    has_clients: bool | None = None

    # Traction signals
    traction_signals: TractionSignals = TractionSignals()

    # Funding signals
    funding_status: FundingStatus = "unknown"
    funding_amount_estimate: str | None = None
    investors_mentioned: list[str] = []

    # Discovery process
    source_channel: str
    search_queries_used: list[str] = []
    discovery_signals: list[str] = []
    discovery_pass: int = 1

    # Dedup node output (Node 6)
    dedup_status: DedupStatus = "genuinely_new"
    possible_duplicate_of: str | None = None
    dedup_signals_matched: list[str] = []

    # Scoring node output (Node 7)
    discovery_value_score: float = 0.0
    discovery_value_reasoning: str = ""

    # Trust & reasoning
    confidence: Confidence = "low"
    confidence_reasoning: str = ""
    evidence: list[EvidenceItem] = []
    red_flags: list[str] = []
    agent_trace: list[str] = []
    recommended_next_step: str = ""
    date_found: str
    status: LeadStatus = "new_lead"


class RunMeta(BaseModel):
    niche: str
    run_date: str
    passes_executed: int
    founder_view: bool


class RunResult(BaseModel):
    run: RunMeta
    results: list[Candidate]
