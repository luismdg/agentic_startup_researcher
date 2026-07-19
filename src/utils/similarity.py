"""Similarity primitives used only by Node 6 (dedup). Deliberately simple and
dependency-light: exact/near-exact string and domain matching plus a
token-overlap fallback for description similarity, upgraded to real OpenAI
embeddings only when OPENAI_API_KEY is configured. None of this is used for
competitive analysis — see Section 6a on why that's out of scope for Node 6."""

import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

from src.config import get_settings


def normalize_domain(url: str | None) -> str | None:
    if not url:
        return None
    candidate = url if "//" in url else f"//{url}"
    host = urlparse(candidate).netloc.lower()
    return host[4:] if host.startswith("www.") else host or None


def domain_match(a: str | None, b: str | None) -> bool:
    da, db = normalize_domain(a), normalize_domain(b)
    return bool(da and db and da == db)


def name_match(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return a.strip().casefold() == b.strip().casefold()


def fuzzy_ratio(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.strip().casefold(), b.strip().casefold()).ratio()


_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def token_overlap(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    tokens_a = set(_WORD_RE.findall(a.lower()))
    tokens_b = set(_WORD_RE.findall(b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


async def description_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    settings = get_settings()
    if settings.openai_enabled:
        try:
            return await _openai_embedding_similarity(a, b, settings.openai_api_key)
        except Exception:
            pass  # fall through to the offline heuristic
    return token_overlap(a, b)


async def _openai_embedding_similarity(a: str, b: str, api_key: str | None) -> float:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    resp = await client.embeddings.create(model="text-embedding-3-small", input=[a, b])
    vec_a, vec_b = resp.data[0].embedding, resp.data[1].embedding
    dot = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = sum(x * x for x in vec_a) ** 0.5
    norm_b = sum(y * y for y in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))
