import pytest

from src.models.candidate import Candidate
from src.models.filters import SearchFilters
from src.models.pipeline import RawCandidate
from src.nodes import niche_adapter, query_generation
from src.nodes.dedup_similarity import dedup
from src.nodes.pipeline import _consolidate_by_startup, _explode_by_founder, _localize_filters, run_pipeline
from src.nodes.questionnaire import resolve_questionnaire
from src.orchestration.localization import localize_terms


def _candidate(founder_name: str, co_founders: list[str] | None = None, **overrides) -> Candidate:
    defaults = dict(
        founder_name=founder_name,
        co_founders=co_founders or [],
        startup_name="Iurefficient",
        website="https://iurefficient.com",
        niche="Mexican LegalTech",
        one_line_description="AI-powered case management for law firms.",
        source_channel="Google search",
        discovery_value_score=50.0,
        date_found="2026-07-18",
    )
    defaults.update(overrides)
    return Candidate(**defaults)


@pytest.mark.asyncio
async def test_pipeline_end_to_end_mock_mode():
    filters = SearchFilters(niche="Mexican LegalTech", geography="Mexico", founder_view=False)
    result = await run_pipeline(filters)

    assert result.run.niche == "Mexican LegalTech"
    assert result.run.passes_executed in (1, 2)
    assert len(result.results) > 0

    for candidate in result.results:
        assert candidate.founder_name
        assert candidate.startup_name
        assert candidate.discovery_value_score >= 0
        assert candidate.confidence in ("low", "medium", "high")
        assert candidate.dedup_status in ("genuinely_new", "possible_duplicate")
        assert len(candidate.agent_trace) > 0

    # Section 6b's own worked example: the low-visibility candidate (bare
    # GitHub repo, no press, no followers) must outrank the more-visible one
    # (launched product, Product Hunt post, some LinkedIn presence).
    by_name = {c.startup_name: c for c in result.results}
    assert "Quetzalli" in by_name
    assert "Lemon Legal" in by_name
    assert by_name["Quetzalli"].discovery_value_score > by_name["Lemon Legal"].discovery_value_score


@pytest.mark.asyncio
async def test_dedup_drops_exact_duplicate():
    exact_duplicate = RawCandidate(
        founder_name="Luis Ramírez",
        startup_name="FyTic",
        website="https://fytic.mx",
        niche="Mexican LegalTech",
        one_line_description="Billing and invoicing automation for Mexican law firms.",
        source_channel="Google search",
        date_found="2026-07-18",
    )
    working, _ = await dedup([exact_duplicate], "Mexican LegalTech")
    assert working == []


@pytest.mark.asyncio
async def test_dedup_flags_possible_duplicate_on_domain_alone():
    domain_only_match = RawCandidate(
        founder_name="Someone Else",
        startup_name="Totally Different Name",
        website="https://fytic.mx",  # same domain as known FyTic, nothing else matches
        niche="Mexican LegalTech",
        one_line_description="An unrelated product with no description overlap.",
        source_channel="Google search",
        date_found="2026-07-18",
    )
    working, _ = await dedup([domain_only_match], "Mexican LegalTech")
    assert len(working) == 1
    assert working[0].dedup_status == "possible_duplicate"
    assert working[0].possible_duplicate_of == "FyTic"


@pytest.mark.asyncio
async def test_dedup_keeps_genuinely_different_candidate():
    unrelated = RawCandidate(
        founder_name="Mariana Cetz",
        startup_name="Quetzalli",
        niche="Mexican LegalTech",
        one_line_description="Automated generation of standard legal documents for notarías.",
        source_channel="Hackathon",
        date_found="2026-07-18",
    )
    working, _ = await dedup([unrelated], "Mexican LegalTech")
    assert len(working) == 1
    assert working[0].dedup_status == "genuinely_new"


@pytest.mark.asyncio
async def test_max_results_caps_output():
    filters = SearchFilters(niche="Mexican LegalTech", geography="Mexico", max_results=1, founder_view=False)
    result = await run_pipeline(filters)
    assert len(result.results) == 1
    # still the highest-scoring candidate, not an arbitrary truncation
    assert result.results[0].startup_name == "Quetzalli"


@pytest.mark.asyncio
async def test_has_clients_filter_narrows_results():
    filters = SearchFilters(niche="Mexican LegalTech", geography="Mexico", has_clients=True, founder_view=False)
    result = await run_pipeline(filters)
    names = {c.startup_name for c in result.results}
    assert "Lemon Legal" in names  # has_clients: true in mock data
    assert "Quetzalli" not in names  # has_clients: false in mock data


def test_questionnaire_returns_niche_specific_fields():
    q = resolve_questionnaire("Mexican LegalTech", "MVP")
    assert q["resolved_via"] == "exact"
    assert "has_clients" in q["recommended_fields"]
    assert "notaría" in q["suggested_keywords"]


def test_questionnaire_falls_back_for_unknown_niche():
    q = resolve_questionnaire("Some Totally Unrecognized Niche", "Idea")
    assert q["niche"] == "Some Totally Unrecognized Niche"
    assert q["resolved_via"] == "generic_default"
    assert "business_model" in q["recommended_fields"]


@pytest.mark.asyncio
async def test_idea_stage_pulls_in_youtube_twitter_reddit():
    # Mexican LegalTech's configured sources don't include youtube/twitter/
    # reddit — stage_signal="Idea" should fold them in on top, and mock data
    # has a candidate on each of those three channels for this niche.
    filters = SearchFilters(
        niche="Mexican LegalTech", geography="Mexico", stage_signal="Idea", max_results=15, founder_view=False
    )
    result = await run_pipeline(filters)
    names = {c.startup_name for c in result.results}
    assert any("despacho" in n.lower() or "notaria" in n.lower() for n in names)


def test_idea_stage_augments_prioritized_sources():
    profile, _ = niche_adapter.resolve_niche_profile("Mexican LegalTech")
    assert "youtube" not in profile.prioritized_sources  # sanity: not there by default

    from src.nodes.pipeline import _augment_sources_for_stage

    augmented, trace = _augment_sources_for_stage(profile, "Idea")
    assert {"youtube", "twitter", "reddit"} <= set(augmented.prioritized_sources)
    assert trace  # logged why

    unaffected, no_trace = _augment_sources_for_stage(profile, "MVP")
    assert "youtube" not in unaffected.prioritized_sources
    assert no_trace == []


def test_query_generation_uses_channel_vocabulary():
    profile, _ = niche_adapter.resolve_niche_profile("Mexican LegalTech")
    filters = SearchFilters(niche="Mexican LegalTech", founder_view=False)
    queries, _ = query_generation.generate_queries(profile, filters, pass_number=1)

    # github's vocabulary includes terms like "hackathon"/"agentic"/"WIP" —
    # distinct from linkedin's "MVP"/"co-founder"/"CEO" — so the generated
    # query text per source should actually differ, not repeat one template.
    github_queries = " ".join(queries.get("github", []))
    linkedin_queries = " ".join(queries.get("linkedin", []))
    assert any(term in github_queries for term in ["hackathon", "agentic", "WIP", "open-source"])
    assert any(term in linkedin_queries for term in ["MVP", "co-founder", "CEO", "founder"])


def test_niche_substring_match_beats_fuzzy_ratio():
    # "LegalTech" scores CLOSER to "Healthtech" than to "Mexican LegalTech"
    # under raw difflib ratio (0.74 vs 0.69) — substring containment must
    # still win, since "LegalTech" is literally inside "Mexican LegalTech".
    profile, trace = niche_adapter.resolve_niche_profile("LegalTech")
    assert profile.niche == "Mexican LegalTech"
    assert profile.resolved_via == "fallback:Mexican LegalTech"
    assert any("substring" in line for line in trace)


def test_niche_substring_match_does_not_over_broaden_to_parent():
    # A confident substring match should resolve to the matched niche
    # itself, not immediately escalate to its configured parent category
    # (that escalation is reserved for genuinely uncertain fuzzy matches).
    profile, _ = niche_adapter.resolve_niche_profile("Mexican legaltech")
    assert profile.niche == "Mexican LegalTech"


@pytest.mark.asyncio
async def test_localize_terms_keeps_jargon_english_translates_business_terms():
    localized, trace = await localize_terms(["SaaS", "MVP", "Law Firms"], "Mexico")
    assert localized[0] == "SaaS"
    assert localized[1] == "MVP"
    assert localized[2] != "Law Firms"
    assert "despacho" in localized[2].lower()
    assert trace


@pytest.mark.asyncio
async def test_localize_terms_noop_for_english_speaking_geography():
    localized, trace = await localize_terms(["Law Firms"], "United States")
    assert localized == ["Law Firms"]
    assert trace == []


@pytest.mark.asyncio
async def test_fytic_scenario_resolves_correct_niche_and_localizes_terms():
    # The exact filter payload from the user's report: niche="LegalTech"
    # (not the canonical "Mexican LegalTech") plus Mexico-specific business
    # terms. Must resolve to Mexican LegalTech, not drift to an unrelated
    # niche, and must localize "Law Firms" for query generation.
    filters = SearchFilters(
        niche="LegalTech",
        geography="Mexico",
        city="Monterrey",
        channels=["LinkedIn", "Google"],
        stage_signal="MVP",
        founded_after=2025,
        business_model="SaaS",
        target_customer="Law Firms",
        funding_stage_filter="bootstrapped",
        max_results=10,
        founder_view=False,
    )
    result = await run_pipeline(filters)

    assert result.run.niche == "LegalTech"  # echoes the user's input niche string
    for candidate in result.results:
        assert candidate.niche == "Mexican LegalTech"  # but actually searched the right one

    localized_filters, _ = await _localize_filters(filters)
    assert localized_filters.business_model == "SaaS"
    assert "despacho" in localized_filters.target_customer.lower()


class _GenuineOnlySettings:
    genuine_only = True


def test_mock_or_none_returns_nothing_when_genuine_only(monkeypatch):
    import src.tools.base as base_module

    monkeypatch.setattr(base_module, "get_settings", lambda: _GenuineOnlySettings())
    candidates, trace = base_module.mock_or_none("google", "Mexican LegalTech", "q", 1, "test reason")
    assert candidates == []
    assert any("GENUINE_RESULTS_ONLY" in line for line in trace)


@pytest.mark.asyncio
async def test_pipeline_returns_nothing_when_genuine_only_and_no_real_capability(monkeypatch):
    # With no API keys configured (this test's hermetic setup) and
    # GENUINE_RESULTS_ONLY on, every channel has zero real capability — the
    # honest answer is an empty result set, never fabricated candidates.
    import src.tools.base as base_module

    monkeypatch.setattr(base_module, "get_settings", lambda: _GenuineOnlySettings())
    filters = SearchFilters(niche="Mexican LegalTech", geography="Mexico", founder_view=False)
    result = await run_pipeline(filters)
    assert result.results == []


def test_extraction_never_concatenates_multiple_founders_into_one_row():
    # The real bug this feature fixes: a single row with founder_name
    # "Eduardo Llaguno Velasco y Frida Velázquez Esquer" is wrong — it must
    # be one founder_name plus one co_founders entry.
    c = _candidate("Eduardo Llaguno Velasco", co_founders=["Frida Velázquez Esquer"])
    assert c.founder_name == "Eduardo Llaguno Velasco"
    assert c.co_founders == ["Frida Velázquez Esquer"]
    assert " y " not in c.founder_name


def test_consolidate_merges_same_startup_found_via_different_founders():
    # Two separate search results for the same startup (same domain), each
    # naming a different co-founder — must merge into one row, not two.
    row_a = _candidate("Eduardo Llaguno Velasco", discovery_value_score=40.0)
    row_b = _candidate("Frida Velázquez Esquer", discovery_value_score=55.0)

    merged, trace = _consolidate_by_startup([row_a, row_b])

    assert len(merged) == 1
    assert merged[0].founder_name == "Frida Velázquez Esquer"  # higher-scoring row wins as base
    assert merged[0].co_founders == ["Eduardo Llaguno Velasco"]
    assert trace


def test_consolidate_leaves_genuinely_different_startups_alone():
    quetzalli = _candidate("Mariana Cetz", startup_name="Quetzalli", website=None)
    lemon = _candidate("Camila Espinoza", startup_name="Lemon Legal", website="https://lemonlegal.mx")

    merged, trace = _consolidate_by_startup([quetzalli, lemon])

    assert len(merged) == 2
    assert trace == []


def test_explode_by_founder_repeats_startup_once_per_founder():
    consolidated = _candidate("Frida Velázquez Esquer", co_founders=["Eduardo Llaguno Velasco"])

    exploded = _explode_by_founder([consolidated])

    assert len(exploded) == 2
    names = {c.founder_name for c in exploded}
    assert names == {"Frida Velázquez Esquer", "Eduardo Llaguno Velasco"}
    for row in exploded:
        assert row.startup_name == "Iurefficient"
        # each row's co_founders lists the OTHER founder(s), not itself
        assert row.founder_name not in row.co_founders


def test_explode_by_founder_is_a_noop_for_single_founder_startups():
    solo = _candidate("Mariana Cetz")
    exploded = _explode_by_founder([solo])
    assert len(exploded) == 1
    assert exploded[0].founder_name == "Mariana Cetz"
    assert exploded[0].co_founders == []


@pytest.mark.asyncio
async def test_run_meta_echoes_founder_view():
    filters = SearchFilters(niche="Mexican LegalTech", geography="Mexico", founder_view=True)
    result = await run_pipeline(filters)
    assert result.run.founder_view is True
