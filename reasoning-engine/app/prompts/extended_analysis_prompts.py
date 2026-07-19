"""
Prompt template for the optional, opt-in extended analysis: End User
Profile, Beachhead Market Analysis, and a 10-criterion Business Segment
scoring table (Bill Aulet-style beachhead segmentation).

Design notes, consistent with scorer_prompts.py / memo_prompts.py:

- Same evidence discipline as the rest of the memo: the fixed evidence pool
  is the only source of company-specific facts; general market/industry
  knowledge is fine for framing but must never be dressed up as a fact
  about THIS company; prefer a data_gap/flag over an invented detail.
- TAM/SAM/SOM/CAGR are treated as *estimates*, not facts -- each becomes a
  TrustedClaim with its own confidence level and reasoning, same as any
  other claim in the memo, rather than a bare authoritative-looking number.
- The 10 segment-scoring criteria are fixed and explained explicitly, with
  the scoring polarity spelled out (5 = most favorable for pursuing that
  segment, on every criterion including the risk-flavored ones) so scores
  are comparable/summable across segments without the model needing to
  decide polarity itself.
- The model proposes candidate segments and scores them; it does NOT rank
  them or declare a winner -- ranking is arithmetic (sum the criteria,
  take the top total), computed in Python in memo_service.py, for the same
  reason axis scores aren't averaged: a ranking that's just "the model's
  opinion" dressed up as a number is exactly the black box this whole
  project is built to avoid.
"""

from __future__ import annotations

import json
from typing import Dict, List

from app.models import AxisScoreSet, CompanyRecord, SEGMENT_CRITERION_LABELS, ThesisConfig
from app.prompts.formatting import format_evidence, format_founders

_CRITERIA_BLOCK = "\n".join(f"- {key}: {label}" for key, label in SEGMENT_CRITERION_LABELS.items())

EXTENDED_ANALYSIS_SYSTEM_PROMPT = f"""You are a venture capital analyst producing an optional, deeper go-to-market \
analysis for a company already covered by a core investment memo. You produce exactly three \
sections: end_user_profile, market_analysis, segment_evaluation.

EVIDENCE DISCIPLINE (same rule as the core memo)
- You are given a fixed set of evidence snippets, each with an id and a reliability tag \
  (primary / secondary / self_reported / inferred). These are the ONLY source of facts about \
  THIS company. General industry/market knowledge is fine for framing but must never be \
  presented as a specific fact about this company.
- Every claim you make in `claims` must have a confidence_level and, where evidence exists, \
  the evidence_ids it rests on. If a field has no supporting evidence or reasonable inference \
  at all, leave it null / empty and add an entry to `data_gaps` instead of guessing.
- Never cite an evidence id that was not given to you.

SECTION 1 -- end_user_profile
The target end user's persona for this company's product. Demographics and psychographics \
should be inferred from the company's stated market/customers where possible; proxy_products \
(what this persona already uses/buys that signals the same need) and watering_holes (where to \
reach them) may draw on reasonable, clearly-labeled industry inference if evidence doesn't \
name them directly -- but must be flagged as inference via a "reasoning" note on the relevant \
claim, not stated as fact. day_in_the_life is a short narrative paragraph. priorities is a \
short list of what this persona optimizes for. Leave any field null/empty rather than inventing \
specifics no evidence or reasonable inference supports.

SECTION 2 -- market_analysis (beachhead market)
primary_end_user and economic_buyer are short role descriptions (who uses it day to day vs who \
approves the budget -- often different people). niche_cagr_pct, tam_usd, sam_usd, som_usd are \
ESTIMATES, not facts -- route each through a claim with confidence_level reflecting how it was \
derived (e.g. "likely" if extrapolated from a stated TAM and a reasonable segment share with \
clear reasoning; "uncertain" or omit with a data_gap if there is no basis to estimate from at \
all). narrative ties the numbers together in a few sentences.

SECTION 3 -- segment_evaluation
Propose 2-4 plausible customer segments this company's product could pursue as a beachhead \
(distinct sub-markets or customer types within its broader sector -- grounded in its actual \
sector, product, and any evidence about who it currently serves or targets). For EACH segment, \
score it 1-5 on EXACTLY these ten criteria, no more, no fewer:
{_CRITERIA_BLOCK}

SCORING POLARITY -- critical: on every criterion, 5 always means "most favorable for pursuing \
this segment," including the risk-flavored ones. For regulatory_risk, 5 means LOW regulatory/ \
liability exposure (favorable), 1 means HIGH exposure (unfavorable). For competitive_intensity, \
5 means LOW competitive intensity or strong differentiation (favorable), 1 means crowded/ \
undifferentiated (unfavorable). Getting this backwards on any criterion makes the segment \
totals meaningless, since they are summed across all ten.

Give each criterion score a one-line justification. Use `flags` on a segment for caveats like \
"scores here are largely analyst judgment, not evidenced" when the company's evidence pool says \
little about that specific segment. Do NOT rank the segments or state which is best -- that is \
computed afterward from your scores, not asked of you.

Respond only with the structured fields requested."""


def build_extended_analysis_messages(
    company: CompanyRecord,
    thesis: ThesisConfig,
    axis_scores: AxisScoreSet,
) -> List[Dict[str, str]]:
    user_prompt = f"""INVESTOR THESIS
- Fund: {thesis.investor_name}
- Sectors: {', '.join(thesis.sectors)} | Stages: {', '.join(thesis.stages)} | \
Geographies: {', '.join(thesis.geographies)}
- Notes: {thesis.notes or '(none)'}

AXIS SCORES (already computed -- use as context, do not contradict them)
- founder: score={axis_scores.founder.score}/10, trend={axis_scores.founder.trend}
- market: score={axis_scores.market.score}/10, trend={axis_scores.market.trend}
- idea_market_fit: score={axis_scores.idea_market_fit.score}/10, trend={axis_scores.idea_market_fit.trend}

COMPANY
- Name: {company.name} | One-liner: {company.one_liner}
- Sector/stage/geo: {company.sector} / {company.stage or 'unknown'} / {company.geography or 'unknown'}

FOUNDERS
{format_founders(company)}

MARKET (raw fields as provided; treat as unverified unless evidence says otherwise)
- Description: {company.market_description or 'not recorded'}
- TAM estimate on file: {company.tam_estimate_usd}
- Named competitors: {', '.join(company.competitors) or 'none recorded'}
- Traction metrics: {json.dumps(company.traction_metrics)}

EVIDENCE POOL (only ids listed here may be cited)
{format_evidence(company)}

Produce end_user_profile, market_analysis, and segment_evaluation now."""

    return [
        {"role": "system", "content": EXTENDED_ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
