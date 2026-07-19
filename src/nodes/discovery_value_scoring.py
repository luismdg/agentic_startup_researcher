"""Node 7 — Discovery-Value Weighting Node (Section 6b). Stage 1 is a gate:
candidates with no checkable anchor never reach scoring. Stage 2 inverts
most normal search-ranking weights — less visibility, younger domains, and
niche (not mainstream) channels score *higher* — while niche relevance
stays a normal positive weight, per the spec's own table."""

from datetime import date

from src.models.pipeline import NicheProfile, RawCandidate, WorkingCandidate
from src.utils.tracing import trace_line

_CHANNEL_WEIGHTS = {
    "hackathon": 1.3,
    "github": 1.25,
    "academic papers": 1.25,
    "youtube": 1.2,
    "twitter/x": 1.25,
    "accelerators": 1.15,
    "community": 1.1,
    "product hunt": 1.0,
    "direct application": 1.0,
    "google search": 0.9,
}
_SCORE_CEILING_MULTIPLIER = 65  # calibrated so a strong cold-start candidate lands ~mid-60s to 90s


def passes_evidence_floor(c: RawCandidate, relaxed: bool = False) -> bool:
    """A candidate must have at least one checkable evidence item with a
    real source_url — never negotiable, even on a broadened pass. Beyond
    that, the strict default accepts either path the spec calls out: a
    concrete anchor (site, repo, LinkedIn profile) OR a named person behind
    an evidence-backed profile — which covers a Reddit/Twitter/YouTube
    handle just as well as a website, since those channels rarely have a
    website/repo/LinkedIn field populated at all. A relaxed broadening pass
    waives even that, requiring only the evidence itself."""
    if not c.evidence or not any(e.source_url for e in c.evidence):
        return False
    if relaxed:
        return True
    has_structured_anchor = bool(c.website or c.traction_signals.github_repo_url or c.founder_linkedin)
    has_named_profile = not c.founder_name.strip().lower().startswith("unknown")
    return has_structured_anchor or has_named_profile


def score(
    candidates: list[WorkingCandidate], profile: NicheProfile, relaxed_floor: bool = False
) -> tuple[list[WorkingCandidate], list[str]]:
    trace: list[str] = []
    survivors: list[WorkingCandidate] = []

    for c in candidates:
        if not passes_evidence_floor(c, relaxed=relaxed_floor):
            trace.append(
                trace_line(
                    f"Node 7 (discovery_value_scoring): '{c.startup_name}' dropped — "
                    "no checkable evidence anchor, does not clear the evidence floor"
                )
            )
            continue

        discovery_value_score, reasoning = _compute_score(c, profile)
        c.discovery_value_score = discovery_value_score
        c.discovery_value_reasoning = reasoning
        trace.append(
            trace_line(f"Node 7: '{c.startup_name}' scored {discovery_value_score} — {reasoning}")
        )
        survivors.append(c)

    return survivors, trace


def _relevance_score(c: WorkingCandidate, profile: NicheProfile) -> float:
    base = 1.0 if c.niche == profile.niche else 0.7
    signal_text = " ".join(c.discovery_signals) + " " + c.one_line_description
    signal_text = signal_text.lower()
    hits = sum(1 for kw in profile.high_weight_signals if _keyword_hit(kw, signal_text))
    return min(1.0, base + min(0.3, hits * 0.1))


def _keyword_hit(keyword_phrase: str, text: str) -> bool:
    words = [w for w in keyword_phrase.replace("/", " ").lower().split() if len(w) >= 4]
    return any(w in text for w in words)


def _visibility_multiplier(c: WorkingCandidate) -> float:
    press = len(c.traction_signals.press_mentions)
    followers = (c.traction_signals.linkedin_followers or 0) + (c.traction_signals.twitter_followers or 0)
    exposure = press * 10 + followers
    return 1.0 / (1.0 + exposure / 50.0)


def _recency_boost(domain_registered_date: str | None) -> float:
    if not domain_registered_date:
        return 0.8
    try:
        registered = date.fromisoformat(domain_registered_date)
    except ValueError:
        return 0.8
    days_old = max(0, (date.today() - registered).days)
    return max(0.5, 1.2 - (days_old / 365) * 0.3)


def _channel_weight(source_channel: str) -> float:
    return _CHANNEL_WEIGHTS.get(source_channel.strip().lower(), 1.0)


def _vc_backing_multiplier(c: WorkingCandidate) -> float:
    return 0.25 if c.investors_mentioned else 1.0


def _compute_score(c: WorkingCandidate, profile: NicheProfile) -> tuple[float, str]:
    relevance = _relevance_score(c, profile)
    visibility = _visibility_multiplier(c)
    recency = _recency_boost(c.domain_registered_date)
    channel = _channel_weight(c.source_channel)
    vc_multiplier = _vc_backing_multiplier(c)

    raw = relevance * visibility * recency * channel * vc_multiplier
    final_score = round(max(0.0, min(100.0, raw * _SCORE_CEILING_MULTIPLIER)), 1)

    parts = []
    if visibility >= 0.85:
        parts.append("little to no press/follower presence — strong cold-start signal")
    elif visibility < 0.4:
        parts.append("notable existing press/follower visibility — likely already on other investors' radar")
    else:
        parts.append("moderate visibility")

    if not c.domain_registered_date:
        parts.append("no domain on record")
    elif recency >= 1.0:
        parts.append("recently registered domain, consistent with a not-yet-discovered project")
    elif recency <= 0.6:
        parts.append("older domain registration lowers novelty")

    if channel >= 1.15:
        parts.append(f"sourced via a niche channel ({c.source_channel})")
    elif channel <= 0.95:
        parts.append(f"sourced via a more mainstream channel ({c.source_channel})")

    if c.investors_mentioned:
        parts.append(f"confirmed prior VC backing ({', '.join(c.investors_mentioned)}) sharply reduces the score")
    else:
        parts.append("no confirmed VC backing found")

    reasoning = "; ".join(parts).capitalize() + "."
    return final_score, reasoning
