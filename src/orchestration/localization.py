"""Localizes filter-derived search terms to the target geography's
language, while keeping recognized global startup jargon in English —
"SaaS", "MVP", "co-founder" are searched in English everywhere, but a term
like "Law Firms" should become "despachos legales" when searching in
Mexico, since that's how a person there actually phrases it. Uses OpenAI
when available (arbitrary terms, arbitrary geographies); falls back to a
small built-in dictionary covering this app's own common filter vocabulary
so mock mode still behaves sensibly with zero configuration."""

import json

from src.config import get_settings
from src.orchestration.client import EXTRACTION_MODEL, get_openai_client
from src.utils.tracing import trace_line

_GEOGRAPHY_LANGUAGES = {
    "mexico": "Spanish",
    "colombia": "Spanish",
    "brazil": "Portuguese",
    "united states": "English",
    "germany": "German",
}

# Global startup/tech jargon that stays in English regardless of geography —
# this is what a real founder/investor would actually search with even when
# writing otherwise in their local language.
_JARGON_ALLOWLIST = {
    "saas", "mvp", "co-founder", "cofounder", "founder", "ceo", "cto", "api",
    "b2b", "b2c", "seed", "pre-seed", "bootstrapped", "series a", "hackathon",
    "demo day", "product-market fit", "startup", "github", "open-source",
}

# Small built-in fallback for this app's own common filter vocabulary, used
# when no OPENAI_API_KEY is configured — enough to keep the app usable with
# zero keys, not a general-purpose translator.
_FALLBACK_TRANSLATIONS = {
    "spanish": {
        "law firms": "despachos legales",
        "law firm": "despacho legal",
        "prototype": "prototipo",
        "clients": "clientes",
        "healthcare": "salud",
        "clinics": "clínicas",
        "small businesses": "pequeñas empresas",
    },
    "portuguese": {
        "law firms": "escritórios de advocacia",
        "law firm": "escritório de advocacia",
        "prototype": "protótipo",
        "clients": "clientes",
        "healthcare": "saúde",
        "small businesses": "pequenas empresas",
    },
    "german": {
        "law firms": "Anwaltskanzleien",
        "law firm": "Anwaltskanzlei",
        "prototype": "Prototyp",
        "clients": "Kunden",
        "healthcare": "Gesundheitswesen",
        "small businesses": "kleine Unternehmen",
    },
}


def _language_for(geography: str | None) -> str | None:
    if not geography:
        return None
    return _GEOGRAPHY_LANGUAGES.get(geography.strip().lower())


async def localize_terms(terms: list[str], geography: str | None) -> tuple[list[str], list[str]]:
    """Returns (localized_terms, trace) — same order and count as `terms`.
    A no-op for empty input, unmapped geographies, or English-speaking ones."""
    trace: list[str] = []
    clean_terms = [t for t in terms if t and t.strip()]
    language = _language_for(geography)
    if not language or language == "English" or not clean_terms:
        return terms, trace

    settings = get_settings()
    if settings.openai_enabled:
        try:
            localized = await _openai_localize(clean_terms, language)
            if len(localized) == len(clean_terms):
                trace.append(
                    trace_line(f"Localized terms to {language} via OpenAI: {clean_terms} -> {localized}")
                )
                return _restore(terms, clean_terms, localized), trace
        except Exception as exc:
            trace.append(trace_line(f"OpenAI localization failed ({exc}) — using built-in fallback"))

    localized = _fallback_localize(clean_terms, language)
    trace.append(trace_line(f"Localized terms to {language} via built-in dictionary: {clean_terms} -> {localized}"))
    return _restore(terms, clean_terms, localized), trace


def _restore(original: list[str], clean: list[str], localized_clean: list[str]) -> list[str]:
    """Re-inserts localized values back into the original list positions,
    leaving any blank/empty entries untouched."""
    mapping = dict(zip(clean, localized_clean))
    return [mapping.get(t, t) if t and t.strip() else t for t in original]


def _fallback_localize(terms: list[str], language: str) -> list[str]:
    table = _FALLBACK_TRANSLATIONS.get(language.lower(), {})
    result = []
    for term in terms:
        if term.strip().lower() in _JARGON_ALLOWLIST:
            result.append(term)
        else:
            result.append(table.get(term.strip().lower(), term))
    return result


async def _openai_localize(terms: list[str], language: str) -> list[str]:
    client = get_openai_client()
    prompt = (
        f"Translate each of these startup-search terms into {language}, for use in local web "
        f"search queries a person in that market would actually type. Keep any term that is "
        f"standard global startup/tech jargon (e.g. SaaS, MVP, co-founder, CEO, API, B2B, seed, "
        f"bootstrapped, hackathon) unchanged in English — only translate genuinely "
        f"descriptive/business terms (e.g. 'Law Firms' -> the natural local phrase, not a "
        f"stilted literal translation). Reply with a JSON object: "
        f'{{"translations": [...]}} — an array of strings, exactly the same order and count as '
        f"the input.\n\nTerms: {json.dumps(terms)}"
    )
    resp = await client.chat.completions.create(
        model=EXTRACTION_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    payload = json.loads(resp.choices[0].message.content or "{}")
    return payload.get("translations", [])
