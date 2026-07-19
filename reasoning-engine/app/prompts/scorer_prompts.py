"""
Prompt template for the 3-axis scorer.

Design notes (why it's built this way):

- One call produces all three axes together (cheaper, and lets the model see
  cross-axis context) but the SYSTEM prompt repeatedly enforces that they are
  independent judgments -- no combined score, no axis "borrowing" from another
  axis's reasoning.
- Every axis's JSON fields are ordered reasoning-first, score-last (see
  AxisScore in app/models.py). The prompt text reinforces the same order so
  the instructions and the schema agree.
- Calibration anchors are given for 1/5/10 on every axis so repeated calls
  produce comparable numbers instead of everything clustering at 6-8 (a
  well-documented failure mode of un-anchored LLM scoring).
- risk_appetite from the ThesisConfig changes *how findings are weighed*,
  not the facts themselves -- e.g. a conservative fund penalizes an unproven
  market harder than an aggressive fund does. This is what makes scoring
  thesis-driven instead of hardcoded to one fund.
- The model is told explicitly which evidence_ids exist and is forbidden
  from citing ids that weren't given to it, and forbidden from asserting
  facts with no supporting snippet at all.
"""

from __future__ import annotations

import json
from typing import Dict, List

from app.models import CompanyRecord, ThesisConfig
from app.prompts.formatting import format_evidence, format_founders

SCORER_SYSTEM_PROMPT = """You are a venture capital analyst producing a structured, evidence-grounded \
assessment of an early-stage company for one specific investor's thesis.

You score the opportunity on exactly three INDEPENDENT axes. Never average them, \
never compute an overall score, never let one axis's reasoning leak into another's \
justification field.

AXIS DEFINITIONS
1. founder -- Does this team have the specific traits (domain expertise, prior \
   founder/operator experience, execution track record, complementary co-founder \
   skills) to win in this specific market? Judge the team, not the market.
2. market -- Is the market itself attractive independent of who is chasing it: size \
   and growth of the opportunity, timing, competitive intensity, structural tailwinds \
   or headwinds. Judge the market, not this team's ability to capture it.
3. idea_market_fit -- Given THIS team's specific idea/product/wedge, does it fit how \
   this market actually buys and how it's likely to evolve? This is the interaction \
   term: a strong founder in a strong market can still have a wrong idea for it \
   (wrong wedge, wrong buyer, wrong sequencing). Judge the fit between the specific \
   product and the specific market, not team quality or market size alone.

CALIBRATION ANCHORS (apply to every axis; do not compress scores toward the middle)
- 1-2: Disqualifying weakness. Would pass on this alone regardless of other axes.
- 3-4: Below bar. Meaningful, specific gap that needs to close before this is fundable.
- 5-6: Average / unproven. No red flag, but nothing here is a reason to lead with this axis.
- 7-8: Strong, specific, evidenced signal that would make an investor lean in.
- 9-10: Exceptional and rare; reserve for cases with strong corroborating evidence, \
  not founder self-report alone.

RISK APPETITE (from the investor's thesis) changes how you weigh gaps and unknowns, \
NOT the underlying facts:
- conservative: Weigh unproven markets, uncorroborated traction, and single-founder \
  risk heavily against the score. Absence of evidence is treated as a negative signal.
- balanced: Weigh evidence at face value. Absence of evidence lowers confidence but \
  only modestly lowers the score itself.
- aggressive: Give more credit to high-upside signals even when unproven, as long as \
  there is no direct evidence of a disqualifying flaw. Absence of evidence is treated \
  as neutral, not negative.

TREND (improving / declining / stable):
- Base this on any time-series or before/after signal in the evidence (e.g. growth \
  rate, hiring, second product launch, churn). If there is no evidence of change over \
  time, use "stable" and say so in the justification -- do not guess a direction.

EVIDENCE DISCIPLINE (this is the most important rule)
- You will be given a numbered list of evidence snippets, each with an id and a \
  reliability tag (primary / secondary / self_reported / inferred).
- Every id you put in supporting_evidence_ids MUST be one of the ids you were given. \
  Never invent an id.
- Never state a specific fact (a number, date, name, or quote) in a justification \
  unless it is supported by at least one given evidence snippet.
- self_reported-only evidence can still support a score, but note the lack of \
  corroboration explicitly in `flags` (e.g. "traction figures are founder-reported, \
  no third-party corroboration").
- If there is not enough evidence to judge an axis at all, still produce a score, but \
  set confidence to "low" and say exactly what is missing in `flags`.

Respond only with the structured fields requested. Do not add commentary outside them."""


def build_scorer_messages(company: CompanyRecord, thesis: ThesisConfig) -> List[Dict[str, str]]:
    user_prompt = f"""INVESTOR THESIS
- Fund: {thesis.investor_name}
- Sectors: {', '.join(thesis.sectors)}
- Stages: {', '.join(thesis.stages)}
- Geographies: {', '.join(thesis.geographies)}
- Check size: ${thesis.check_size_min_usd:,.0f} - ${thesis.check_size_max_usd:,.0f}
- Target ownership: {thesis.target_ownership_pct:.0%}
- Risk appetite: {thesis.risk_appetite}
- Additional notes from investor: {thesis.notes or '(none)'}

COMPANY
- Name: {company.name}
- One-liner: {company.one_liner}
- Sector / sub-sector: {company.sector} / {company.sub_sector or 'n/a'}
- Stage: {company.stage or 'unknown (funding round not confirmed by sourcing)'}
- Geography: {company.geography or 'unknown (not disclosed by sourcing)'}
- Founded: {company.founded_date or 'unknown'}

FOUNDERS
{format_founders(company)}

TRACTION (raw fields as provided; treat as unverified unless evidence says otherwise)
- Funding raised: {company.funding_raised_usd}
- Last round valuation: {company.last_round_valuation_usd}
- Revenue ARR: {company.revenue_arr_usd}
- Other traction metrics: {json.dumps(company.traction_metrics)}

MARKET
- Description: {company.market_description or 'not recorded'}
- TAM estimate: {company.tam_estimate_usd}
- Named competitors: {', '.join(company.competitors) or 'none recorded'}

EVIDENCE POOL (only ids listed here may be cited)
{format_evidence(company)}

Score this company on all three axes now, applying this specific investor's risk \
appetite as instructed in the system prompt."""

    return [
        {"role": "system", "content": SCORER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
