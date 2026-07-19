"""Shared serialization helpers used by both prompt templates.

Kept in one place so the scorer and the memo generator always describe a
company's founders/evidence to the model identically -- if the memo's view of
the evidence pool ever drifted from the scorer's, the two calls could reach
inconsistent conclusions about the same facts.
"""

from app.models import CompanyRecord


def format_evidence(company: CompanyRecord) -> str:
    lines = []
    for ev in company.evidence_pool:
        lines.append(
            f"- id={ev.id} | reliability={ev.reliability} | source={ev.source}\n"
            f"  \"{ev.snippet_text}\""
        )
    return "\n".join(lines) if lines else "(no evidence snippets attached)"


def format_founders(company: CompanyRecord) -> str:
    lines = []
    for f in company.founders:
        exits = ", ".join(f.prior_exits) if f.prior_exits else "none recorded"
        lines.append(
            f"- {f.name} ({f.role}): {f.background_summary or 'no background summary recorded'}; "
            f"prior exits: {exits}; evidence_ids referencing them: {f.evidence_ids}"
        )
    return "\n".join(lines) if lines else "(no founder records)"
