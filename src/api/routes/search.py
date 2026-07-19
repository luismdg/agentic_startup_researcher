from fastapi import APIRouter

from src.models.candidate import RunResult
from src.models.filters import SearchFilters
from src.nodes.pipeline import run_pipeline
from src.nodes.questionnaire import resolve_questionnaire

router = APIRouter()


@router.post("")
async def search(filters: SearchFilters) -> RunResult:
    return await run_pipeline(filters)


@router.get("/questionnaire")
def questionnaire(niche: str, stage_signal: str | None = None) -> dict:
    return resolve_questionnaire(niche, stage_signal)
