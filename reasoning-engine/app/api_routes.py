"""
JSON API for frontend_vcBrain to consume live -- the "full live integration"
path: ingest raw sourcing records, run the orchestrator, and serve the
results shaped exactly like frontend_vcBrain's mock data
(lib/types.ts: Startup / Screening / TrustScoreRecord / Memo).

Kept as its own router (not folded into main.py's Jinja routes) because it
has a different job: main.py serves this backend's own minimal HTML UI,
this module serves a different frontend entirely. Same underlying pipeline
either way -- app/services/orchestrator.py -- so the two UIs can never
disagree about what a company scored.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.mock_data import DEMO_THESIS
from app.models import SourcingSearchResponse
from app.services.frontend_shaping import to_memo_json, to_screening_json, to_startup_json, to_trust_score_json
from app.services.orchestrator import PipelineResult, run_pipeline

router = APIRouter(prefix="/api")

# company_id -> (PipelineResult, original SourcingResult). Demo cache, process
# memory only -- same tradeoff as main.py's caches, first thing to swap for
# real storage later.
_pipeline_cache: dict[str, tuple[PipelineResult, object]] = {}


@router.post("/sourcing/ingest")
def ingest_sourcing_results(payload: SourcingSearchResponse):
    """Runs the full pipeline (adapt -> thesis fit -> score -> memo) for
    every result in the payload and caches it. This is the expensive call
    (2 real LLM calls per record) -- callers should ingest deliberately, not
    on every page load."""
    thesis = DEMO_THESIS
    created = []
    for sourcing_record in payload.results:
        result = run_pipeline(sourcing_record, thesis)
        _pipeline_cache[result.company.id] = (result, sourcing_record)
        created.append({"id": result.company.id, "name": result.company.name})
    return {"ingested": len(created), "startups": created}


@router.get("/startups")
def list_startups():
    return [to_startup_json(result, record) for result, record in _pipeline_cache.values()]


@router.get("/startups/{startup_id}/screening")
def get_screening(startup_id: str):
    entry = _pipeline_cache.get(startup_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"no orchestrated pipeline result for '{startup_id}'")
    result, _ = entry
    return to_screening_json(result)


@router.get("/startups/{startup_id}/trust")
def get_trust_score(startup_id: str):
    entry = _pipeline_cache.get(startup_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"no orchestrated pipeline result for '{startup_id}'")
    result, _ = entry
    return to_trust_score_json(result)


@router.get("/startups/{startup_id}/memo")
def get_memo(startup_id: str):
    entry = _pipeline_cache.get(startup_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"no orchestrated pipeline result for '{startup_id}'")
    result, _ = entry
    return to_memo_json(result)
