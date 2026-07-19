from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """One-time filter submission from the frontend's guided search panel —
    not a conversational input. `niche` and `stage_signal` drive which of
    the richer attributes below actually matter (see
    src/nodes/questionnaire.py / GET /search/questionnaire) — but every
    field is always accepted here, so the frontend can submit the full form
    in one shot regardless of which fields it chose to surface. `keywords`
    is the always-available free-text escape hatch on top of every other
    filter. Values for niche/geography/channels/stage_signal are validated
    against /data/filter-options.json in Node 1, not hardcoded here.
    `founder_view` is required — see its own docstring below."""

    # Core
    niche: str
    geography: str | None = None
    city: str | None = None
    channels: list[str] = []
    stage_signal: str | None = None
    keywords: list[str] = []

    # Required: which unit each result row represents.
    #   True  -> founder-centric: one row per founder. The same startup can
    #            legitimately repeat across rows if it has multiple co-founders.
    #   False -> startup-centric: one row per startup. Co-founders are
    #            consolidated into that single row's `co_founders` list and
    #            never appear as separate, repeated rows.
    founder_view: bool

    # Company/product attributes
    founded_after: int | None = None
    founded_before: int | None = None
    has_clients: bool | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    business_model: str | None = None
    target_customer: str | None = None
    tech_stack: list[str] = []
    funding_stage_filter: str | None = None  # e.g. "bootstrapped" — filters candidates, distinct
    # from the output field of the same name on each result

    max_results: int = Field(default=10, ge=1, le=15)
