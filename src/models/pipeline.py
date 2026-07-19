"""Internal-only models used between pipeline nodes. Never returned directly
to the API caller — Node 8 (evidence_assembly) maps these into Candidate."""

from pydantic import BaseModel

from src.models.candidate import (
    Confidence,
    DedupStatus,
    EvidenceItem,
    FundingStatus,
    ProductStage,
    TractionSignals,
)


class NicheProfile(BaseModel):
    niche: str
    prioritized_sources: list[str]
    query_templates: list[str]
    high_weight_signals: list[str] = []
    evidence_floor: str = "at least one live site OR one verifiable founder profile"
    fallback_parent_niche: str | None = None
    secondary_niches: list[str] = []
    resolved_via: str = "exact"  # "exact" | "fallback:<parent>" | "generic_default"
    questionnaire: dict = {}  # see src/nodes/questionnaire.py


class RawCandidate(BaseModel):
    """What a tool call in Node 4 produces, before dedup/scoring/assembly."""

    founder_name: str
    co_founders: list[str] = []
    founder_city: str | None = None
    founder_country: str | None = None
    founder_linkedin: str | None = None
    founder_education: str | None = None
    founder_prior_ventures: list[str] = []
    startup_name: str
    website: str | None = None
    domain_registered_date: str | None = None
    estimated_founded_year: int | None = None

    niche: str
    one_line_description: str
    product_stage: ProductStage = "unknown"
    team_size_estimate: int | None = None
    tech_stack_signals: list[str] = []
    has_clients: bool | None = None

    traction_signals: TractionSignals = TractionSignals()

    funding_status: FundingStatus = "unknown"
    funding_amount_estimate: str | None = None
    investors_mentioned: list[str] = []

    source_channel: str
    search_queries_used: list[str] = []
    discovery_signals: list[str] = []
    discovery_pass: int = 1

    evidence: list[EvidenceItem] = []
    trace: list[str] = []
    date_found: str


class WorkingCandidate(RawCandidate):
    """RawCandidate plus the Node 6/7 outputs, before Node 9 (confidence &
    red flags) finalizes it into a Candidate."""

    dedup_status: DedupStatus = "genuinely_new"
    possible_duplicate_of: str | None = None
    dedup_signals_matched: list[str] = []

    discovery_value_score: float = 0.0
    discovery_value_reasoning: str = ""
