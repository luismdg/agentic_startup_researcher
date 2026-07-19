"""
FastAPI entrypoint: dashboard (ranked list) + memo detail view.

Scoring and memo generation are lazy and cached in-memory, keyed by
(company_id, thesis_id) -- so switching the active ThesisConfig naturally
invalidates the cache (a company scored under one fund's lens says nothing
about another fund's lens) without needing an explicit cache-bust step.
This is a demo cache (process memory, not persisted); fine for a hackathon,
first thing to swap for real storage afterward.

Run with:  uvicorn app.main:app --reload   (from the reasoning-engine/ dir)
Requires:  ANTHROPIC_API_KEY (default) or, with LLM_PROVIDER=openai set,
           OPENAI_API_KEY -- see app/services/llm_client.py.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_routes import router as api_router
from app.mock_data import COMPANIES, DEMO_THESIS
from app.models import ThesisConfig
from app.services.memo_service import generate_extended_analysis, generate_memo
from app.services.scorer_service import score_company
from app.services.thesis_engine import evaluate_thesis_fit

app = FastAPI(title="Reasoning & Experience")
# frontend_vcBrain runs on the Next.js dev server (localhost:3000) and fetches
# this API cross-origin; CORS only needs to allow that one local dev origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

_companies_by_id = {c.id: c for c in COMPANIES}

# Swap this for a real thesis store/selector later; every downstream call
# already takes a ThesisConfig as an argument, so nothing else has to change.
_active_thesis = DEMO_THESIS

_score_cache: dict[tuple[str, str], object] = {}
_memo_cache: dict[tuple[str, str], object] = {}
_extended_cache: dict[tuple[str, str], object] = {}


def _get_or_score(company: object, thesis: ThesisConfig):
    key = (company.id, thesis.id)
    if key not in _score_cache:
        _score_cache[key] = score_company(company, thesis)
    return _score_cache[key]


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    thesis = _active_thesis
    rows = []
    for company in COMPANIES:
        fit = evaluate_thesis_fit(company, thesis)
        rows.append({
            "company": company,
            "fit": fit,
            "scores": _score_cache.get((company.id, thesis.id)),
        })
    # Ranked: thesis-passing companies first, then by founder+market+idea avg
    # score (display-only ordering; the 3 axes are never averaged INTO a
    # stored score, this is just a sort key for the list view).
    def sort_key(row):
        passes = row["fit"].passes_hard_filters
        scores = row["scores"]
        avg = (
            (scores.founder.score + scores.market.score + scores.idea_market_fit.score) / 3
            if scores else -1
        )
        return (not passes, -avg)

    rows.sort(key=sort_key)
    return templates.TemplateResponse(
        request, "dashboard.html", {"thesis": thesis, "rows": rows}
    )


@app.post("/score/{company_id}")
def trigger_score(company_id: str):
    company = _companies_by_id[company_id]
    _get_or_score(company, _active_thesis)
    return RedirectResponse(url="/", status_code=303)


@app.get("/memo/{company_id}", response_class=HTMLResponse)
def memo_view(request: Request, company_id: str, extended: bool = False):
    thesis = _active_thesis
    company = _companies_by_id[company_id]
    key = (company_id, thesis.id)

    if key not in _memo_cache:
        axis_scores = _get_or_score(company, thesis)
        fit = evaluate_thesis_fit(company, thesis)
        _memo_cache[key] = generate_memo(company, thesis, axis_scores, fit)

    memo = _memo_cache[key]

    # Extended analysis (End User Profile / Beachhead Market / Business
    # Segments) is an extra LLM call -- only made when ?extended=1 is
    # explicitly requested, so viewing a memo never silently costs more
    # than the 2 calls (score + memo) it already costs today.
    if extended and key not in _extended_cache:
        axis_scores = _get_or_score(company, thesis)
        end_user_profile, market_analysis, segment_evaluation = generate_extended_analysis(
            company, thesis, axis_scores
        )
        _extended_cache[key] = (end_user_profile, market_analysis, segment_evaluation)

    if key in _extended_cache:
        memo.end_user_profile, memo.market_analysis, memo.segment_evaluation = _extended_cache[key]

    evidence_by_id = {ev.id: ev for ev in company.evidence_pool}
    return templates.TemplateResponse(
        request,
        "memo.html",
        {
            "thesis": thesis,
            "company": company,
            "memo": memo,
            "evidence_by_id": evidence_by_id,
            "extended_requested": extended,
        },
    )
