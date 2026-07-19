"""
Prompt template for the investment memo generator.

Design notes:

- Takes the already-computed AxisScoreSet and ThesisFitResult as INPUT rather
  than re-deriving them. This keeps one source of truth: the memo narrative
  cannot say something that contradicts the numbers shown on the dashboard,
  because both come from the same upstream call.
- The LLM only returns MemoDraft (5 sections). Axis scores, thesis fit, and
  the trust summary tally are assembled around it in Python -- see
  app/services/memo_service.py.
- The claim-level trust mechanism is the crux of "not a black box": every
  sentence in a section that asserts a checkable fact must show up in that
  section's `claims` list with a confidence_level + evidence_ids. Anything
  that would require a claim but has no evidence becomes a `data_gaps` entry
  instead of a sentence -- the model is told to prefer omission over
  invention, every time.
"""

from __future__ import annotations

import json
from typing import Dict, List

from app.models import AxisScoreSet, CompanyRecord, ThesisConfig, ThesisFitResult
from app.prompts.formatting import format_evidence, format_founders

MEMO_SYSTEM_PROMPT = """You are a venture capital associate drafting an investment memo for a partner \
meeting. You write tightly, in the voice of a memo, not marketing copy. You are \
allergic to invented facts.

You must produce exactly five sections: company_snapshot, investment_hypotheses, \
swot, problem_product, traction_kpis.

problem_product is the one section with two fields instead of one: `problem` (the \
structural problem this company's target customer has, independent of this company's \
own product) and `product` (specifically how THIS company's product addresses that \
problem). Write them as genuinely different paragraphs -- `product` must not restate \
`problem` in different words, and neither should just repeat the other. If you truly \
cannot say anything about the product beyond what's already evidenced for the problem, \
say so plainly in `product` (e.g. "No product detail beyond the one-liner is evidenced") \
rather than duplicating `problem`'s text to fill the field.

HARD RULES ON FACTS AND CLAIMS
1. You are given a fixed set of evidence snippets, each with an id and a reliability \
   tag (primary / secondary / self_reported / inferred). These are the ONLY source of \
   facts you may use. General knowledge about the sector or market is fine for framing \
   ("fintech reconciliation is a known pain point for mid-market companies") but must \
   never be dressed up as a fact about THIS company.
2. Every sentence in a section's `content` (or, for problem_product, in either `problem` \
   or `product`) that states a specific, checkable fact about the company (a number, date, \
   name, quote, revenue figure, customer count, prior exit, cap table detail, etc.) must \
   have a matching entry in that section's `claims` list: the exact claim text, a \
   confidence_level, the evidence_ids it rests on, and a one-line reasoning for that \
   confidence level.
3. Confidence level rubric for each claim:
   - "verified": corroborated by 2+ independent evidence snippets, OR by a single \
     "primary" reliability snippet.
   - "likely": a single "secondary" reliability snippet, or a direct, non-speculative \
     inference from a primary/secondary snippet.
   - "uncertain": "self_reported" evidence only, with no corroboration.
   - "unverifiable": use only if you must mention something the memo structure requires \
     but there is truly no evidence for it -- prefer rule 4 instead whenever possible.
4. If a required topic (e.g. cap table, revenue, prior exits) has NO supporting evidence \
   at all, do NOT invent a placeholder or hedge with vague language. Instead add a \
   `data_gaps` entry to that section using the literal pattern "<Topic>: not disclosed" \
   (or "not evidenced" if it's a claim rather than a document, e.g. "Customer retention: \
   not evidenced") and simply do not write a sentence asserting it in `content`.
5. investment_hypotheses must explicitly connect to the investor's thesis (check size, \
   ownership target, sector/stage fit, risk appetite) and to the axis scores/trends you \
   are given -- do not restate generic bull points that would apply to any company.
6. swot entries are short claim-like bullets (a phrase or one sentence each), each still \
   backed by a claims-style confidence + evidence_ids, or explicitly framed as analyst \
   judgment with confidence_level "unverifiable" and reasoning noting it is inference, \
   not a sourced fact (e.g. a structural market threat you're inferring, not quoting).
7. Never cite an evidence id that was not given to you.

Write content as plain prose (a few sentences per section is enough; this is a working \
memo, not a press release). Respond only with the structured fields requested."""


def build_memo_messages(
    company: CompanyRecord,
    thesis: ThesisConfig,
    axis_scores: AxisScoreSet,
    thesis_fit: ThesisFitResult,
) -> List[Dict[str, str]]:
    def axis_block(name: str, a) -> str:
        return (
            f"- {name}: score={a.score}/10, trend={a.trend}, confidence={a.confidence}\n"
            f"  justification: {a.justification}\n"
            f"  flags: {a.flags}"
        )

    user_prompt = f"""INVESTOR THESIS
- Fund: {thesis.investor_name}
- Sectors: {', '.join(thesis.sectors)} | Stages: {', '.join(thesis.stages)} | \
Geographies: {', '.join(thesis.geographies)}
- Check size: ${thesis.check_size_min_usd:,.0f} - ${thesis.check_size_max_usd:,.0f}
- Target ownership: {thesis.target_ownership_pct:.0%} | Risk appetite: {thesis.risk_appetite}
- Notes: {thesis.notes or '(none)'}

THESIS FIT (already computed, do not recompute -- use as context for investment_hypotheses)
- Passes hard filters: {thesis_fit.passes_hard_filters} (failures: {thesis_fit.hard_filter_failures or 'none'})
- Ownership feasibility: {thesis_fit.ownership_feasibility} -- {thesis_fit.ownership_note}
- Risk alignment: {thesis_fit.risk_alignment_note}

AXIS SCORES (already computed, do not recompute -- reference these, do not contradict them)
{axis_block('founder', axis_scores.founder)}
{axis_block('market', axis_scores.market)}
{axis_block('idea_market_fit', axis_scores.idea_market_fit)}

COMPANY
- Name: {company.name} | One-liner: {company.one_liner}
- Sector/stage/geo: {company.sector} / {company.stage or 'unknown (funding round not confirmed by sourcing)'} / {company.geography or 'unknown (not disclosed by sourcing)'}
- Founded: {company.founded_date or 'unknown'}

FOUNDERS
{format_founders(company)}

TRACTION (raw fields; only usable in a claim if an evidence snippet backs the specific number)
- Funding raised: {company.funding_raised_usd}
- Last round valuation: {company.last_round_valuation_usd}
- Revenue ARR: {company.revenue_arr_usd}
- Other traction metrics: {json.dumps(company.traction_metrics)}
- Cap table disclosed: {company.cap_table_disclosed} (detail: {company.cap_table})

MARKET
- Description: {company.market_description or 'not recorded'}
- TAM estimate: {company.tam_estimate_usd}
- Named competitors: {', '.join(company.competitors) or 'none recorded'}

EVIDENCE POOL (only ids listed here may be cited; reliability tag shown for each)
{format_evidence(company)}

Draft the five memo sections now."""

    return [
        {"role": "system", "content": MEMO_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
