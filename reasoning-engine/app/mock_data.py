"""
Stand-in for the handoff from the Memory/Sourcing layer.

Swap this module for a real loader (DB query / API call into your teammate's
service) once it exists. As long as it returns `CompanyRecord` objects with
the same field names, nothing downstream (scoring, memo, UI) has to change --
that's the whole point of building against the schema instead of a live
dependency.
"""

from datetime import datetime

from app.models import CompanyRecord, EvidenceSnippet, FounderRecord, ThesisConfig

DEMO_THESIS = ThesisConfig(
    id="thesis_demo",
    investor_name="Northstar Seed Fund",
    sectors=["fintech", "devtools"],
    stages=["pre_seed", "seed"],
    geographies=["US", "Canada"],
    check_size_min_usd=250_000,
    check_size_max_usd=1_500_000,
    target_ownership_pct=0.08,
    risk_appetite="balanced",
    notes="Prefer technical founding teams with at least one prior startup, even if it didn't exit.",
)

COMPANIES = [
    CompanyRecord(
        id="co_atlas",
        name="Atlas Ledger",
        one_liner="Reconciliation infra for fintech APIs.",
        sector="fintech",
        stage="seed",
        geography="US",
        founded_date="2024-02-01",
        founders=[
            FounderRecord(
                id="f_1",
                name="Priya Nair",
                role="CEO",
                linkedin_url="https://linkedin.com/in/example-priya",
                background_summary="Ex-Plaid infra engineer, 5 yrs. First-time founder.",
                prior_exits=[],
                education=["BS CS, Waterloo"],
                evidence_ids=["ev_atlas_1", "ev_atlas_2"],
            ),
        ],
        funding_raised_usd=900_000,
        last_round_valuation_usd=8_000_000,
        revenue_arr_usd=180_000,
        traction_metrics={"active_customers": 6, "mom_growth": 0.22},
        market_description="Mid-market fintechs need reconciliation between ledgers and payment processors.",
        tam_estimate_usd=2_500_000_000,
        competitors=["Modern Treasury", "in-house scripts"],
        cap_table_disclosed=False,
        cap_table=None,
        founder_score=7.2,
        cold_start_tier="tier_2_partial",
        evidence_pool=[
            EvidenceSnippet(
                id="ev_atlas_1",
                source="LinkedIn",
                source_url="https://linkedin.com/in/example-priya",
                snippet_text="5 years at Plaid, Senior Infra Engineer, led reconciliation pipeline team.",
                retrieved_at=datetime(2026, 6, 1),
                reliability="secondary",
            ),
            EvidenceSnippet(
                id="ev_atlas_2",
                source="Founder call transcript",
                snippet_text="Priya: 'We closed 6 paying customers, ARR is about 180k, growing roughly 20% month over month for the last 3 months.'",
                retrieved_at=datetime(2026, 6, 10),
                reliability="self_reported",
            ),
            EvidenceSnippet(
                id="ev_atlas_3",
                source="Crunchbase",
                source_url="https://crunchbase.com/organization/atlas-ledger",
                snippet_text="Atlas Ledger raised a $900K seed round in March 2025.",
                retrieved_at=datetime(2026, 6, 1),
                reliability="secondary",
            ),
        ],
        last_updated=datetime(2026, 6, 15),
    ),
    CompanyRecord(
        id="co_fabra",
        name="Fabra",
        one_liner="LLM eval tooling for regulated industries.",
        sector="devtools",
        stage="pre_seed",
        geography="US",
        founded_date="2025-01-15",
        founders=[
            FounderRecord(
                id="f_2",
                name="Daniel Osei",
                role="CEO",
                background_summary="Second-time founder. Prior company (Reko) shut down after 2 years, no exit.",
                prior_exits=[],
                education=["MS Statistics, UChicago"],
                evidence_ids=["ev_fabra_1"],
            ),
        ],
        funding_raised_usd=150_000,
        last_round_valuation_usd=None,
        revenue_arr_usd=None,
        traction_metrics={},
        market_description="Compliance teams at banks need auditable LLM eval trails.",
        tam_estimate_usd=None,
        competitors=["Braintrust", "internal tooling"],
        cap_table_disclosed=False,
        cap_table=None,
        founder_score=5.5,
        cold_start_tier="tier_3_cold",
        evidence_pool=[
            EvidenceSnippet(
                id="ev_fabra_1",
                source="Pitch deck p.2",
                snippet_text="Daniel previously founded Reko (2021-2023), a data-labeling startup that wound down.",
                retrieved_at=datetime(2026, 6, 5),
                reliability="self_reported",
            ),
        ],
        last_updated=datetime(2026, 6, 12),
    ),
]
