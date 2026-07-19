"""
Runs the 3-axis scorer prompt and turns the result into a stored AxisScoreSet.

Evidence-id sanitization here is defense in depth: the prompt already
forbids citing an id that wasn't given (see scorer_prompts.py), but a prompt
instruction is not a guarantee. If the model cites an id outside the
company's evidence_pool anyway, we strip it and record the fact in `flags`
rather than silently trusting or silently dropping it -- consistent with
"every score is explainable, not a black box."
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models import AxisScore, AxisScoreSet, AxisScoreSetDraft, CompanyRecord, ThesisConfig
from app.prompts.scorer_prompts import build_scorer_messages
from app.services.llm_client import call_structured


def _sanitize_axis(axis: AxisScore, valid_ids: set[str]) -> None:
    bad_ids = [i for i in axis.supporting_evidence_ids if i not in valid_ids]
    if bad_ids:
        axis.supporting_evidence_ids = [i for i in axis.supporting_evidence_ids if i in valid_ids]
        axis.flags.append(f"dropped unknown evidence id(s) the model cited but were not provided: {bad_ids}")


def score_company(company: CompanyRecord, thesis: ThesisConfig) -> AxisScoreSet:
    messages = build_scorer_messages(company, thesis)
    draft = call_structured(messages, AxisScoreSetDraft)

    valid_ids = {ev.id for ev in company.evidence_pool}
    for axis in draft.founder, draft.market, draft.idea_market_fit:
        _sanitize_axis(axis, valid_ids)

    return AxisScoreSet(
        company_id=company.id,
        thesis_id=thesis.id,
        generated_at=datetime.now(timezone.utc),
        founder=draft.founder,
        market=draft.market,
        idea_market_fit=draft.idea_market_fit,
    )
