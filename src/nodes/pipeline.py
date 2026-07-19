"""Orchestrates Nodes 1-10, including Section 7's multi-pass adaptive logic.
Pass 1 runs the niche's default query set; if it yields too few viable
candidates the system broadens automatically (secondary niches + a relaxed
evidence floor) for Pass 2, and if it yields too many it identifies the
dominant differentiating attribute among the results as a narrowing signal.
Either way, passes are merged before dedup — the caller only ever sees one
final list, per the spec's "invisible plumbing" requirement (Node 10)."""

from collections import Counter
from datetime import date

from src.models.candidate import Candidate, RunMeta, RunResult
from src.models.filters import SearchFilters
from src.models.pipeline import NicheProfile, RawCandidate
from src.nodes import confidence_flagging, dedup_similarity, discovery_value_scoring, evidence_assembly
from src.nodes import filter_intake, niche_adapter, query_generation
from src.nodes.multi_source_fetch import fetch, trivial_pool_dedup
from src.orchestration.localization import localize_terms
from src.services.data_store import append_known_startups
from src.utils.similarity import normalize_domain
from src.utils.tracing import trace_line

BROADEN_THRESHOLD = 2  # fewer viable candidates than this after Pass 1 -> broaden
NARROW_THRESHOLD = 8  # more viable candidates than this after Pass 1 -> flag for narrowing

# Idea-stage founders often show up on these channels long before a company
# site or repo exists — building-in-public content, demo videos, feedback
# threads. Folded in whenever the stage is early/unknown, on top of whatever
# the niche profile already prioritizes (see _augment_sources_for_stage).
_IDEA_STAGE_SOURCES = ["youtube", "twitter", "reddit"]
_IDEA_STAGE_SIGNALS = {None, "Idea", "Unknown"}


async def run_pipeline(filters: SearchFilters) -> RunResult:
    run_trace: list[str] = []

    filters, t = filter_intake.intake(filters)
    run_trace += t

    profile, t = niche_adapter.resolve_niche_profile(filters.niche)
    run_trace += t

    profile, t = _augment_sources_for_stage(profile, filters.stage_signal)
    run_trace += t

    localized_filters, t = await _localize_filters(filters)
    run_trace += t

    filters_context = _build_filters_context(filters)

    all_raw: list[RawCandidate] = []
    passes_executed = 1
    relaxed_floor = False

    for pass_number in (1, 2):
        passes_executed = pass_number
        extra_niches = profile.secondary_niches if pass_number == 2 and relaxed_floor else None

        queries, t = query_generation.generate_queries(profile, localized_filters, pass_number, extra_niches)
        run_trace += t
        queries, t = await query_generation.maybe_llm_diversify_queries(queries, profile.niche)
        run_trace += t

        fetched, t = await fetch(queries, profile.niche, pass_number, filters_context)
        run_trace += t
        all_raw.extend(fetched)

        pooled, t = trivial_pool_dedup(all_raw)
        run_trace += t
        viable = [c for c in pooled if discovery_value_scoring.passes_evidence_floor(c)]

        if pass_number == 1:
            if len(viable) < BROADEN_THRESHOLD:
                relaxed_floor = True
                run_trace.append(
                    trace_line(
                        f"Pass 1 returned only {len(viable)} viable candidate(s) — broadening with "
                        f"secondary niches {profile.secondary_niches} and a relaxed evidence floor for Pass 2"
                    )
                )
                continue
            if len(viable) > NARROW_THRESHOLD:
                dominant = _dominant_attribute(viable)
                run_trace.append(
                    trace_line(
                        f"Pass 1 returned {len(viable)} candidates — dominant differentiating attribute "
                        f"is {dominant}; a narrower Pass 2 would filter on it, but the current source set "
                        "already exhausted its query templates, so results are merged as-is"
                    )
                )
                break
            run_trace.append(
                trace_line(f"Pass 1 returned {len(viable)} candidates — no broadening or narrowing needed")
            )
            break

    pooled, t = trivial_pool_dedup(all_raw)
    run_trace += t

    working, t = await dedup_similarity.dedup(pooled, profile.niche)
    run_trace += t

    scored, t = discovery_value_scoring.score(working, profile, relaxed_floor=relaxed_floor)
    run_trace += t

    assembled = evidence_assembly.assemble(scored, run_trace)
    flagged, _ = confidence_flagging.flag(assembled)

    flagged, _ = _apply_user_filters(flagged, filters)

    # Always consolidate to one row per startup first — this is the
    # canonical unit for both dedup memory and correctness (two different
    # searches surfacing two different co-founders of the same startup
    # should never look like two different startups). founder_view then
    # decides what the *caller* sees: startup-view returns this as-is,
    # founder-view explodes it back out into one row per founder.
    consolidated, t = _consolidate_by_startup(flagged)
    run_trace += t

    _persist_new_startups(consolidated)

    output = _explode_by_founder(consolidated) if filters.founder_view else consolidated

    output.sort(key=lambda c: c.discovery_value_score, reverse=True)
    output = output[: filters.max_results]

    return RunResult(
        run=RunMeta(
            niche=filters.niche,
            run_date=date.today().isoformat(),
            passes_executed=passes_executed,
            founder_view=filters.founder_view,
        ),
        results=output,
    )


def _augment_sources_for_stage(profile: NicheProfile, stage_signal: str | None) -> tuple[NicheProfile, list[str]]:
    """MVP/Launched stages lean on the niche's own configured sources
    (GitHub, Product Hunt, accelerators...) — but idea-stage founders are
    likeliest to show up on YouTube/Twitter/Reddit first, regardless of
    niche, so those get folded in whenever the stage is early or unspecified."""
    trace: list[str] = []
    if stage_signal not in _IDEA_STAGE_SIGNALS:
        return profile, trace

    missing = [s for s in _IDEA_STAGE_SOURCES if s not in profile.prioritized_sources]
    if not missing:
        return profile, trace

    trace.append(
        trace_line(
            f"Node 2: stage_signal='{stage_signal}' — adding idea-stage channels {missing} "
            "on top of the niche's configured sources"
        )
    )
    return profile.model_copy(update={"prioritized_sources": profile.prioritized_sources + missing}), trace


async def _localize_filters(filters: SearchFilters) -> tuple[SearchFilters, list[str]]:
    """Translates the free-text filter fields that actually feed into query
    wording (business_model, target_customer, keywords, tech_stack) into the
    target geography's language, via src/orchestration/localization.py —
    global startup jargon ("SaaS", "MVP") stays in English, descriptive
    terms ("Law Firms") become what a local searcher would actually type.
    One batched call covers every field to avoid firing off several small
    OpenAI requests per search."""
    singleton_fields = [f for f in ("business_model", "target_customer") if getattr(filters, f)]
    terms = [getattr(filters, f) for f in singleton_fields] + list(filters.keywords) + list(filters.tech_stack)
    if not terms:
        return filters, []

    localized, trace = await localize_terms(terms, filters.geography)

    updates: dict = {}
    idx = 0
    for field in singleton_fields:
        updates[field] = localized[idx]
        idx += 1
    n_keywords = len(filters.keywords)
    updates["keywords"] = localized[idx : idx + n_keywords]
    idx += n_keywords
    updates["tech_stack"] = localized[idx:]

    return filters.model_copy(update=updates), trace


def _build_filters_context(filters: SearchFilters) -> str:
    """A plain-language summary of the richer filter attributes, threaded
    through to Node 3 (query wording) and the OpenAI web-research agent's
    prompt (src/orchestration/web_research_agent.py)."""
    parts = []
    if filters.city:
        parts.append(f"city: {filters.city}")
    if filters.founded_after:
        parts.append(f"founded after {filters.founded_after}")
    if filters.founded_before:
        parts.append(f"founded before {filters.founded_before}")
    if filters.has_clients is True:
        parts.append("must already have paying clients/users")
    elif filters.has_clients is False:
        parts.append("prefer pre-revenue/no clients yet")
    if filters.team_size_min:
        parts.append(f"team size at least {filters.team_size_min}")
    if filters.team_size_max:
        parts.append(f"team size at most {filters.team_size_max}")
    if filters.business_model:
        parts.append(f"business model: {filters.business_model}")
    if filters.target_customer:
        parts.append(f"target customer: {filters.target_customer}")
    if filters.tech_stack:
        parts.append(f"tech stack: {', '.join(filters.tech_stack)}")
    if filters.funding_stage_filter:
        parts.append(f"funding stage: {filters.funding_stage_filter}")
    if filters.keywords:
        parts.append(f"additional keywords: {', '.join(filters.keywords)}")
    return "; ".join(parts)


def _apply_user_filters(
    candidates: list[Candidate], filters: SearchFilters
) -> tuple[list[Candidate], list[str]]:
    """Hard-filters on the richer attributes — only when both the filter is
    set AND the candidate's value is known. Never drops a candidate purely
    for missing data; that would undercut the cold-start bias (Section 3)."""
    trace: list[str] = []
    kept: list[Candidate] = []

    for c in candidates:
        if (
            filters.founded_after
            and c.estimated_founded_year is not None
            and c.estimated_founded_year < filters.founded_after
        ):
            trace.append(trace_line(f"Filter: dropped '{c.startup_name}' — founded before {filters.founded_after}"))
            continue
        if (
            filters.founded_before
            and c.estimated_founded_year is not None
            and c.estimated_founded_year > filters.founded_before
        ):
            trace.append(trace_line(f"Filter: dropped '{c.startup_name}' — founded after {filters.founded_before}"))
            continue
        if filters.has_clients is not None and c.has_clients is not None and c.has_clients != filters.has_clients:
            trace.append(trace_line(f"Filter: dropped '{c.startup_name}' — has_clients mismatch"))
            continue
        if (
            filters.team_size_min
            and c.team_size_estimate is not None
            and c.team_size_estimate < filters.team_size_min
        ):
            trace.append(trace_line(f"Filter: dropped '{c.startup_name}' — team smaller than {filters.team_size_min}"))
            continue
        if (
            filters.team_size_max
            and c.team_size_estimate is not None
            and c.team_size_estimate > filters.team_size_max
        ):
            trace.append(trace_line(f"Filter: dropped '{c.startup_name}' — team larger than {filters.team_size_max}"))
            continue
        if (
            filters.funding_stage_filter
            and c.funding_status != "unknown"
            and c.funding_status != filters.funding_stage_filter
        ):
            trace.append(trace_line(f"Filter: dropped '{c.startup_name}' — funding_status mismatch"))
            continue
        kept.append(c)

    return kept, trace


def _consolidate_by_startup(candidates: list[Candidate]) -> tuple[list[Candidate], list[str]]:
    """One row per unique startup (matched by domain, falling back to exact
    startup name — same signal as Node 5's trivial pool dedup). When two
    rows turn out to be the same startup, they're merged into the
    higher-scoring one, with every named founder from both combined into a
    single deduplicated founder_name + co_founders list — never dropped,
    never left as separate repeated rows."""
    trace: list[str] = []
    groups: dict[str, list[Candidate]] = {}
    order: list[str] = []

    for c in candidates:
        key = normalize_domain(c.website) if c.website else f"name:{c.startup_name.strip().casefold()}"
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(c)

    merged: list[Candidate] = []
    for key in order:
        group = groups[key]
        if len(group) == 1:
            merged.append(group[0])
            continue

        group.sort(key=lambda c: c.discovery_value_score, reverse=True)
        base = group[0]
        all_founders: list[str] = []
        for c in group:
            for name in [c.founder_name, *c.co_founders]:
                if name and name not in all_founders:
                    all_founders.append(name)
        primary, *rest = all_founders

        trace.append(
            trace_line(
                f"Consolidated {len(group)} results for '{base.startup_name}' into one row — "
                f"founders: {all_founders}"
            )
        )
        merged.append(base.model_copy(update={"founder_name": primary, "co_founders": rest}))

    return merged, trace


def _explode_by_founder(candidates: list[Candidate]) -> list[Candidate]:
    """founder_view=True: turn each startup-consolidated row back into one
    row per named founder, so a startup with N co-founders legitimately
    appears N times — once per founder, each row's co_founders listing the
    others for context."""
    exploded: list[Candidate] = []
    for c in candidates:
        all_founders = [c.founder_name, *c.co_founders]
        if len(all_founders) <= 1:
            exploded.append(c)
            continue
        for name in all_founders:
            siblings = [n for n in all_founders if n != name]
            exploded.append(c.model_copy(update={"founder_name": name, "co_founders": siblings}))
    return exploded


def _dominant_attribute(candidates: list[RawCandidate]) -> str:
    counts = Counter(c.funding_status for c in candidates)
    if not counts:
        return "funding_status=unknown"
    attr, n = counts.most_common(1)[0]
    return f"funding_status={attr} ({n}/{len(candidates)})"


def _persist_new_startups(candidates: list[Candidate]) -> None:
    to_persist = [
        {
            "startup_name": c.startup_name,
            "website": c.website,
            "founder_name": c.founder_name,
            "co_founders": c.co_founders,
            "niche": c.niche,
            "one_line_description": c.one_line_description,
            "first_seen": c.date_found,
        }
        for c in candidates
        if c.dedup_status == "genuinely_new" and c.confidence in ("medium", "high")
    ]
    append_known_startups(to_persist)
