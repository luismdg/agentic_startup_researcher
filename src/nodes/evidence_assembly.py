"""Node 8 — Evidence Assembly. Builds the final Candidate object (Section 8
schema) for each surviving candidate. Trust fields (confidence, red_flags,
recommended_next_step, status) are left at their defaults here — Node 9
fills them in, matching the spec's node order (8 then 9)."""

from src.models.candidate import Candidate
from src.models.pipeline import WorkingCandidate


def assemble(working: list[WorkingCandidate], run_trace: list[str]) -> list[Candidate]:
    assembled = []
    for wc in working:
        data = wc.model_dump(exclude={"trace"})
        data["agent_trace"] = [*run_trace, *wc.trace]
        assembled.append(Candidate(**data))
    return assembled
