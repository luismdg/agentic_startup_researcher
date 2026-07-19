"""Node 3 — Query Generation. Builds a diverse query set per source: a
direct-match query from the niche profile, the user's own keyword/business/
target-customer attributes, a founder-first variant for people-centric
sources, a vocabulary variant using that channel's own terminology (people
describe the same thing differently on LinkedIn vs. GitHub vs. Reddit — see
src/data/channel-vocabulary.json), and (on a broadening pass) adjacent-niche
variants. The LLM diversification path is optional and only runs when
OPENAI_API_KEY is configured — the pipeline never depends on it."""

from src.config import get_settings
from src.models.filters import SearchFilters
from src.models.pipeline import NicheProfile
from src.services.data_store import load_channel_vocabulary
from src.utils.tracing import trace_line

_FOUNDER_FIRST_SOURCES = {"google", "linkedin"}


def generate_queries(
    profile: NicheProfile,
    filters: SearchFilters,
    pass_number: int,
    extra_niches: list[str] | None = None,
) -> tuple[dict[str, list[str]], list[str]]:
    trace: list[str] = []
    templates = profile.query_templates or [f"{profile.niche} startup founder"]
    geography_suffix = f" {filters.geography}" if filters.geography else ""
    if filters.city:
        geography_suffix += f" {filters.city}"

    keyword_bits = list(filters.keywords)
    if filters.business_model:
        keyword_bits.append(filters.business_model)
    if filters.target_customer:
        keyword_bits.append(filters.target_customer)
    keyword_bits.extend(filters.tech_stack)
    keyword_suffix = f" {' '.join(keyword_bits)}" if keyword_bits else ""

    vocabulary = load_channel_vocabulary()

    queries: dict[str, list[str]] = {}
    for i, source in enumerate(profile.prioritized_sources):
        base = templates[i % len(templates)]
        source_queries = [f"{base}{geography_suffix}".strip()]

        if source in _FOUNDER_FIRST_SOURCES:
            source_queries.append(f"{profile.niche} founder{geography_suffix}".strip())

        if keyword_suffix:
            source_queries.append(f"{profile.niche}{keyword_suffix}{geography_suffix}".strip())

        vocab_labels = vocabulary.get(source, {}).get("typical_labels", [])[:2]
        if vocab_labels:
            source_queries.append(f"{profile.niche} {' '.join(vocab_labels)}{geography_suffix}".strip())

        for adjacent in extra_niches or []:
            source_queries.append(f"{adjacent} startup founder{geography_suffix}".strip())

        queries[source] = source_queries
        trace.append(
            trace_line(f"Node 3 (query_generation): pass {pass_number} [{source}] -> {source_queries}")
        )

    return queries, trace


async def maybe_llm_diversify_queries(
    queries: dict[str, list[str]], niche: str
) -> tuple[dict[str, list[str]], list[str]]:
    settings = get_settings()
    trace: list[str] = []
    if not settings.openai_enabled or not queries:
        return queries, trace

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        prompt = (
            f"Suggest one additional, differently-phrased web search query for finding "
            f"early-stage, low-visibility startup founders in the niche '{niche}'. "
            "Reply with only the query text, no quotes or explanation."
        )
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=40,
        )
        variant = (resp.choices[0].message.content or "").strip()
        if variant:
            for source_queries in queries.values():
                source_queries.append(variant)
            trace.append(trace_line(f"Node 3: LLM-diversified query added: '{variant}'"))
    except Exception as exc:
        trace.append(trace_line(f"Node 3: LLM diversification skipped ({exc})"))

    return queries, trace
