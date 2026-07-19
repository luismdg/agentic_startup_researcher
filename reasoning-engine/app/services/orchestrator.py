"""
Single entry point that turns one raw sourcing record into a fully reasoned
result: adapt -> thesis fit -> 3-axis score -> memo. This is what "SOURCING
record in, one combined object out" means concretely -- everything else in
app/services/ is a stage this function calls in order, once each, so there
is exactly one place that defines the pipeline shape.

Deliberately a plain function, not a class: there is no state to hold
between calls (caching lives in main.py, which is a presentation-layer
concern, not a pipeline concern) and every stage is already independently
testable via its own service module.
"""

from __future__ import annotations

from app.models import AxisScoreSet, CompanyRecord, InvestmentMemo, SourcingResult, ThesisConfig, ThesisFitResult
from app.services.memo_service import generate_memo
from app.services.scorer_service import score_company
from app.services.sourcing_adapter import adapt_sourcing_result
from app.services.thesis_engine import evaluate_thesis_fit


class PipelineResult:
    """Everything produced for one sourcing record under one thesis. Not a
    Pydantic model -- it's an internal bundle for main.py to shape into
    whatever a caller (Jinja template, JSON API) actually needs, not a
    schema meant to be serialized as-is."""

    def __init__(
        self,
        company: CompanyRecord,
        thesis_fit: ThesisFitResult,
        axis_scores: AxisScoreSet,
        memo: InvestmentMemo,
    ):
        self.company = company
        self.thesis_fit = thesis_fit
        self.axis_scores = axis_scores
        self.memo = memo


def run_pipeline(sourcing_record: SourcingResult, thesis: ThesisConfig) -> PipelineResult:
    company = adapt_sourcing_result(sourcing_record)
    thesis_fit = evaluate_thesis_fit(company, thesis)
    axis_scores = score_company(company, thesis)
    memo = generate_memo(company, thesis, axis_scores, thesis_fit)
    return PipelineResult(company=company, thesis_fit=thesis_fit, axis_scores=axis_scores, memo=memo)
