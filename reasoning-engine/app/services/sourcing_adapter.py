"""
Adapter: teammate's raw Agentic Sourcing Search output -> CompanyRecord.

CompanyRecord (app/models.py) is the schema the scorer, memo generator, and
thesis engine all consume, and it's designed to stay stable regardless of
where the data comes from. The sourcing schema (SourcingResult, also in
app/models.py) is richer in some places (agent_trace, search_queries_used,
per-lead confidence) and thinner in others (no revenue, no confirmed funding
numbers, no cap table) -- this module resolves that mismatch once, so
nothing downstream has to know the sourcing schema exists.

Deliberate choices, and why:
- product_stage ("idea"/"mvp"/"launched") is NOT the same axis as
  CompanyRecord.stage (a funding round). They're conflated in casual
  language but are different facts; mapping product_stage into
  CompanyRecord.stage would silently assert a funding round nobody
  confirmed. CompanyRecord.stage is derived from funding_status instead,
  and left None when funding_status is "bootstrapped"/"unknown" -- an
  honest "we don't know the round" rather than a guessed one.
- funding_amount_estimate is a fuzzy string (e.g. "~$50K (unconfirmed)").
  Parsing it into CompanyRecord.funding_raised_usd would assert a precision
  the source doesn't have. It's kept as evidence text instead, so the
  scorer/memo treat it with the same skepticism they apply to any
  self-reported/unconfirmed number.
- discovery_signals, red_flags, confidence_reasoning, and
  discovery_value_reasoning become evidence snippets with
  reliability="inferred" -- they're the sourcing agent's own
  observations/judgment, not a quoted external source, which is exactly
  what "inferred" means in EvidenceSnippet.reliability.
- discovery_value_score is deliberately NOT written into
  CompanyRecord.founder_score. It measures how hard-to-find/low-visibility
  a candidate is (Node 7 of the sourcing pipeline) -- a sourcing-process
  metric, not a judgment of founder or company quality. Conflating the two
  would let a well-hidden but mediocre candidate look identical to a
  well-hidden, strong one. It's carried as evidence text instead, so the
  scorer can weigh it as context without it masquerading as a score.
- co_founders become additional FounderRecords, never merged into a single
  founder_name string -- same reasoning the sourcing service itself gives
  for keeping them separate (see its founder_view mode).
- has_clients becomes a traction evidence snippet when the sourcing service
  actually knows the answer (True or False); left out entirely when null,
  same "don't invent, don't imply an unknown as a no" rule as everywhere
  else in this adapter.
- dedup_status="possible_duplicate" becomes an evidence note (with
  possible_duplicate_of and the matched signals), not a silent drop -- the
  sourcing service itself already hard-drops exact duplicates before this
  ever reaches the adapter; "possible" ones are a real signal worth the
  scorer seeing, not hiding.
- founder_score / cold_start_tier are intentionally left None here -- those
  belong to the teammate's Founder Score / cold-start tiering step, a
  separate stage of the Memory/Sourcing layer, not this adapter.
- competitors is left empty: the real sourcing schema has no
  "similar competitors found" field (an earlier doc-only draft of this
  schema had one; the actual running service does not) -- nothing to map.
- Pure process metadata (search_queries_used, agent_trace, source_channel,
  recommended_next_step, status, date_found, discovery_pass) describes HOW
  the lead was found, not a fact ABOUT the company -- intentionally not
  carried into CompanyRecord/EvidenceSnippet, which are both company-facts
  schemas. If a future "how this lead was found" UI is wanted, adapt from
  SourcingResult directly rather than smuggling it through CompanyRecord.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from typing import List, Optional

from app.models import CompanyRecord, EvidenceSnippet, FounderRecord, SourcingResult, SourcingSearchResponse

_FUNDING_STATUS_TO_STAGE = {
    "pre-seed": "pre_seed",
    "seed": "seed",
    # "bootstrapped" and "unknown" deliberately unmapped -- see module docstring.
}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "company"


def _company_id(result: SourcingResult) -> str:
    fingerprint = (result.website or result.founder_linkedin or result.startup_name).encode()
    short_hash = hashlib.sha1(fingerprint).hexdigest()[:6]
    return f"co_{_slugify(result.startup_name)}_{short_hash}"


def _as_utc_datetime(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)


def _evidence_reliability(source_url: str, result: SourcingResult) -> str:
    if result.website and source_url.startswith(result.website):
        return "self_reported"  # the company's own site describing itself
    return "secondary"  # third-party platform/press, not a verified filing


class _EvidenceBuilder:
    """Accumulates EvidenceSnippets with sequential, collision-free ids."""

    def __init__(self, company_id: str):
        self.company_id = company_id
        self.items: List[EvidenceSnippet] = []

    def add(
        self,
        source: str,
        snippet_text: str,
        reliability: str,
        source_url: Optional[str] = None,
        captured: Optional[datetime] = None,
    ) -> str:
        eid = f"ev_{self.company_id}_{len(self.items) + 1}"
        self.items.append(EvidenceSnippet(
            id=eid,
            source=source,
            source_url=source_url,
            snippet_text=snippet_text,
            retrieved_at=captured or datetime.now(timezone.utc),
            reliability=reliability,
        ))
        return eid


def adapt_sourcing_result(result: SourcingResult) -> CompanyRecord:
    company_id = _company_id(result)
    evidence = _EvidenceBuilder(company_id)

    founder_evidence_ids = []
    for item in result.evidence:
        eid = evidence.add(
            source=item.source_url,
            snippet_text=item.snippet,
            reliability=_evidence_reliability(item.source_url, result),
            source_url=item.source_url,
            captured=_as_utc_datetime(item.date_captured),
        )
        if result.founder_linkedin and result.founder_linkedin in item.source_url:
            founder_evidence_ids.append(eid)

    for signal in result.discovery_signals:
        evidence.add("Sourcing agent -- discovery signal", signal, "inferred")

    for flag in result.red_flags:
        evidence.add("Sourcing agent -- red flag", flag, "inferred")

    if result.confidence_reasoning:
        evidence.add("Sourcing agent -- confidence assessment", result.confidence_reasoning, "inferred")

    if result.discovery_value_reasoning:
        evidence.add(
            "Sourcing agent -- discovery value assessment",
            f"(discovery_value_score={result.discovery_value_score:.1f}/100) {result.discovery_value_reasoning}",
            "inferred",
        )

    if result.dedup_status == "possible_duplicate":
        matched = ", ".join(result.dedup_signals_matched) or "no specific signals recorded"
        evidence.add(
            "Sourcing agent -- dedup check",
            f"Flagged as a possible duplicate of '{result.possible_duplicate_of}' ({matched}). "
            "Not dropped, but corroboration should be treated cautiously until confirmed distinct.",
            "inferred",
        )

    if result.funding_amount_estimate:
        evidence.add(
            "Sourcing agent -- funding estimate (unconfirmed)",
            f"Estimated funding: {result.funding_amount_estimate}",
            "inferred",
        )

    if result.has_clients is not None:
        evidence.add(
            "Sourcing agent -- client status",
            "Has active/paying clients." if result.has_clients else "No clients found/confirmed.",
            "inferred",
        )

    for job in result.traction_signals.job_postings_found:
        evidence.add("Job posting", job, "secondary")

    for mention in result.traction_signals.press_mentions:
        evidence.add("Press mention", mention, "secondary")

    if result.traction_signals.github_commit_activity:
        evidence.add(
            "GitHub",
            result.traction_signals.github_commit_activity,
            "secondary",
            source_url=result.traction_signals.github_repo_url,
        )

    traction_metrics = {}
    if result.traction_signals.linkedin_followers is not None:
        traction_metrics["linkedin_followers"] = float(result.traction_signals.linkedin_followers)
    if result.traction_signals.twitter_followers is not None:
        traction_metrics["twitter_followers"] = float(result.traction_signals.twitter_followers)
    if result.team_size_estimate is not None:
        traction_metrics["team_size_estimate"] = float(result.team_size_estimate)

    primary_founder = FounderRecord(
        id=f"f_{company_id}_1",
        name=result.founder_name,
        role="Founder",  # not disclosed by the sourcing schema
        linkedin_url=result.founder_linkedin,
        background_summary=result.founder_education,
        prior_exits=result.founder_prior_ventures,
        education=[result.founder_education] if result.founder_education else [],
        evidence_ids=founder_evidence_ids,
    )
    # co_founders arrive as bare names only (no linkedin/education/prior
    # ventures per-person in this schema) -- represented as minimal
    # FounderRecords rather than merged into founder_name, same "never
    # merge co-founders into one string" rule the sourcing service itself
    # follows internally.
    co_founders = [
        FounderRecord(id=f"f_{company_id}_{i + 2}", name=name, role="Co-founder")
        for i, name in enumerate(result.co_founders)
    ]

    return CompanyRecord(
        id=company_id,
        name=result.startup_name,
        one_liner=result.one_line_description,
        sector=result.niche,  # freeform text; thesis_engine matches this by keyword, not equality
        stage=_FUNDING_STATUS_TO_STAGE.get(result.funding_status),
        geography=result.founder_country,  # may be None; thesis_engine treats that as an explicit unknown
        founded_date=result.domain_registered_date,  # only ever a real recorded date, never a guessed one
        founders=[primary_founder, *co_founders],
        funding_raised_usd=None,  # never parsed from a fuzzy estimate string, see module docstring
        last_round_valuation_usd=None,
        revenue_arr_usd=None,
        traction_metrics=traction_metrics,
        market_description=None,  # not distinctly provided by this schema; scorer relies on evidence instead
        tam_estimate_usd=None,
        competitors=[],  # the real sourcing schema has no competitor field to map, see module docstring
        cap_table_disclosed=False,
        cap_table=None,
        founder_score=None,  # filled by teammate's cold-start tiering step, not this adapter
        cold_start_tier=None,
        evidence_pool=evidence.items,
        last_updated=_as_utc_datetime(result.date_found),
    )


def adapt_sourcing_response(response: SourcingSearchResponse) -> List[CompanyRecord]:
    return [adapt_sourcing_result(result) for result in response.results]