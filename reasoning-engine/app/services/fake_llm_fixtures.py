"""
Canned, schema-valid responses for LLM_PROVIDER=fake.

Exists so the whole pipeline -- dashboard, scoring trigger, memo rendering,
trust bar, claim chips -- can be exercised for $0 before spending real API
credit. Every string is prefixed "[FAKE]" so it's never mistaken for a real
model judgment if it ends up on screen during a demo.

evidence_ids are deliberately left empty rather than pointing at a specific
mock company's snippet ids: this fixture is shared across every company in
mock_data.py, and scorer_service.py / memo_service.py already sanitize (and
flag) any cited id that isn't in the target company's evidence_pool -- empty
avoids tripping that on every single fake call.
"""

from __future__ import annotations

import itertools
from typing import Any, Callable, Dict

from app.models import SEGMENT_CRITERION_LABELS

# claim_id must be unique per call (consumers, including frontend_vcBrain,
# use it as a React list key) -- a text-prefix-derived id collided across
# claims sharing an opening phrase like "[FAKE] sample ...". A monotonic
# counter side-steps that regardless of how similar the placeholder text is.
_claim_counter = itertools.count(1)


def _fake_claim(text: str, confidence: str) -> Dict[str, Any]:
    return {
        "claim_id": f"fake_{next(_claim_counter)}",
        "claim_text": text,
        "confidence_level": confidence,
        "evidence_ids": [],
        "reasoning": "[FAKE] placeholder reasoning, no real model call was made.",
    }


def _fake_axis_score_set_draft() -> Dict[str, Any]:
    def axis(name: str, score: int) -> Dict[str, Any]:
        return {
            "axis": name,
            "key_factors": ["[FAKE] placeholder factor A", "[FAKE] placeholder factor B"],
            "supporting_evidence_ids": [],
            "justification": f"[FAKE] placeholder justification for {name}, no real model call was made.",
            "flags": ["fake provider -- not a real assessment"],
            "confidence": "low",
            "trend": "stable",
            "score": score,
        }

    return {
        "founder": axis("founder", 6),
        "market": axis("market", 6),
        "idea_market_fit": axis("idea_market_fit", 6),
    }


def _fake_memo_draft() -> Dict[str, Any]:
    def section(title: str) -> Dict[str, Any]:
        return {
            "title": title,
            "content": f"[FAKE] placeholder {title} narrative -- LLM_PROVIDER=fake, no credit spent.",
            "claims": [_fake_claim(f"[FAKE] sample claim for {title}", "uncertain")],
            "data_gaps": [f"{title}: not evidenced (fake provider)"],
        }

    return {
        "company_snapshot": section("Company snapshot"),
        "investment_hypotheses": section("Investment hypotheses"),
        "swot": {
            "strengths": [_fake_claim("[FAKE] sample strength", "uncertain")],
            "weaknesses": [_fake_claim("[FAKE] sample weakness", "uncertain")],
            "opportunities": [_fake_claim("[FAKE] sample opportunity", "unverifiable")],
            "threats": [_fake_claim("[FAKE] sample threat", "unverifiable")],
        },
        "problem_product": {
            "problem": "[FAKE] placeholder problem narrative -- LLM_PROVIDER=fake, no credit spent.",
            "product": "[FAKE] placeholder product narrative -- deliberately different text from the problem field.",
            "claims": [_fake_claim("[FAKE] sample claim for Problem & product", "uncertain")],
            "data_gaps": ["Problem & product: not evidenced (fake provider)"],
        },
        "traction_kpis": section("Traction & KPIs"),
    }


def _fake_extended_analysis_draft() -> Dict[str, Any]:
    criteria = [
        {
            "criterion": key,
            "score": 3,
            "justification": f"[FAKE] placeholder score for {label.lower()}.",
        }
        for key, label in SEGMENT_CRITERION_LABELS.items()
    ]

    return {
        "end_user_profile": {
            "demographics": "[FAKE] placeholder demographics -- no real model call was made.",
            "psychographics": "[FAKE] placeholder psychographics.",
            "proxy_products": ["[FAKE] proxy product A", "[FAKE] proxy product B"],
            "watering_holes": ["[FAKE] watering hole A"],
            "day_in_the_life": "[FAKE] placeholder day-in-the-life narrative.",
            "priorities": ["[FAKE] priority A", "[FAKE] priority B"],
            "claims": [_fake_claim("[FAKE] sample end-user claim", "uncertain")],
            "data_gaps": ["Watering holes: not evidenced (fake provider)"],
        },
        "market_analysis": {
            "primary_end_user": "[FAKE] placeholder primary end user.",
            "economic_buyer": "[FAKE] placeholder economic buyer.",
            "niche_cagr_pct": 12.0,
            "tam_usd": 1_000_000_000.0,
            "sam_usd": 200_000_000.0,
            "som_usd": 20_000_000.0,
            "narrative": "[FAKE] placeholder beachhead market narrative -- LLM_PROVIDER=fake.",
            "claims": [_fake_claim("[FAKE] sample TAM/SAM/SOM claim", "uncertain")],
            "data_gaps": [],
        },
        "segment_evaluation": {
            "segments": [
                {
                    "segment_name": "[FAKE] Segment A",
                    "description": "[FAKE] placeholder segment description.",
                    "criteria": criteria,
                    "flags": ["fake provider -- not a real assessment"],
                },
                {
                    "segment_name": "[FAKE] Segment B",
                    "description": "[FAKE] placeholder segment description.",
                    "criteria": criteria,
                    "flags": ["fake provider -- not a real assessment"],
                },
            ],
        },
    }


FAKE_BUILDERS: Dict[str, Callable[[], Dict[str, Any]]] = {
    "AxisScoreSetDraft": _fake_axis_score_set_draft,
    "MemoDraft": _fake_memo_draft,
    "ExtendedAnalysisDraft": _fake_extended_analysis_draft,
}
