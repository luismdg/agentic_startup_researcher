# VC Brain — Orchestration Design

This is the technical reference for how a request actually flows through the system: the 10-node
pipeline, the OpenAI orchestration layer, the tools/data layers. For the request/response JSON
contract (what to send to `POST /search`, what you get back), see `API.md`. For setup/run
instructions, see `README.md`.

---

## 1. What this is

A FastAPI service that takes a one-time filter submission and runs a 10-node discovery pipeline
that actively searches the live web (via an OpenAI agentic browsing layer) across multiple
channels — GitHub, Google, LinkedIn, Twitter/X, YouTube, Reddit, Product Hunt, accelerator
directories, arXiv — for early-stage, low-visibility startups/founders matching a niche. It
returns a ranked, deduplicated list, favoring hard-to-find candidates over well-documented ones.
Two endpoints, `GET /search/questionnaire` and `POST /search` — see `API.md` for their exact
request/response shapes.

---

## 2. Orchestration design

### 2.1 Pipeline overview

```
 SearchFilters (frontend request — see API.md for the JSON shape)
        │
 [Node 1] Filter Intake              src/nodes/filter_intake.py
        │   validates against filter-options.json, never hard-rejects
        ▼
 [Node 2] Niche Adapter              src/nodes/niche_adapter.py
        │   exact match → substring match → fuzzy match → generic default
        │   + stage-based source augmentation (src/nodes/pipeline.py)
        │     idea-stage adds youtube/twitter/reddit on top of the niche's sources
        ▼
 [pre-pass] Term Localization        src/orchestration/localization.py
        │   business_model/target_customer/keywords/tech_stack translated to the
        │   geography's language; global startup jargon (SaaS, MVP, ...) stays English
        ▼
 ┌──── Pass loop (1–2 passes, Section 7 adaptive broadening/narrowing) ────┐
 │ [Node 3] Query Generation         src/nodes/query_generation.py         │
 │      per source: base → keyword → founder-first →                       │
 │      channel-vocabulary (src/data/channel-vocabulary.json) →            │
 │      optional LLM diversification                                       │
 │           │                                                             │
 │ [Node 4] Multi-Source Fetch       src/nodes/multi_source_fetch.py       │
 │      parallel fan-out to src/tools/*.py (see 2.3 below)                 │
 │           │                                                             │
 │ [Node 5] Raw Candidate Pool       trivial_pool_dedup() in Node 4's file │
 │      URL/exact-name dedup only — real similarity dedup is Node 6        │
 │           │                                                             │
 │      too few viable? → broaden (secondary niches + relaxed evidence     │
 │      floor) and run pass 2. too many? → log dominant differentiator.    │
 └───────────────────────────────────────────────────────────────────────┘
        ▼
 [Node 6] Dedup / Similarity          src/nodes/dedup_similarity.py
        │   weighted match against src/data/known-startups.json (domain > founder
        │   name > fuzzy startup name > description similarity) — 3-way split:
        │   duplicate (dropped) | possible_duplicate (flagged, continues) | genuinely_new
        ▼
 [Node 7] Discovery-Value Scoring     src/nodes/discovery_value_scoring.py
        │   Stage 1 gate: must have ≥1 evidence item + (structured anchor OR named profile)
        │   Stage 2: inverted weighting — less visibility/younger domain/niche channel
        │   score HIGHER; niche relevance and confirmed VC backing are not inverted
        ▼
 [Node 8] Evidence Assembly           src/nodes/evidence_assembly.py
        │   WorkingCandidate → Candidate (Section 8 schema)
        ▼
 [Node 9] Confidence & Red Flags      src/nodes/confidence_flagging.py
        │   confidence from evidence corroboration; red flags from internal
        │   inconsistencies (e.g. 9-day-old domain, claimed team of 10)
        ▼
 [user filters] founded_after/before, has_clients, team_size, funding_stage_filter
        │   src/nodes/pipeline.py::_apply_user_filters — only excludes on a KNOWN mismatch
        ▼
 [consolidate] one row per startup, always                src/nodes/pipeline.py
        │   merges co-founders found via separate searches into one row;
        │   persists genuinely_new/medium+confidence results to known-startups.json
        ▼
 [Node 10] Output — founder_view decides the final shape
        │   false → startup-centric rows as-is
        │   true  → _explode_by_founder(): one row per named founder
        ▼
 sorted by discovery_value_score, truncated to max_results
        ▼
 [post] Fallback Candidate (plan C)   src/nodes/pipeline.py::_apply_fallback_candidate
        │   always on — appends one hardcoded, clearly-labeled candidate only if
        │   genuine search found nothing for it
        ▼
 RunResult
```

### 2.2 Orchestration library — `src/orchestration/`

This is what makes sources "real" instead of mocked, using only `OPENAI_API_KEY`.

- **`client.py`** — cached `AsyncOpenAI` client, model constants.
- **`web_research_agent.py`** — `research_channel(query, niche, channel, filters_context,
  max_results, discovery_pass)`. Two separate model calls, not one (asking a tool-using model to
  browse *and* emit strict JSON in the same turn is unreliable):
  1. **Browse** — Responses API call with the hosted web-search tool
     (`tools=[{"type": "web_search_preview"}]`, falling back to `"web_search"` if the account's
     API version names it differently). The prompt is framed per-channel from
     `src/data/channel-vocabulary.json` — the same "early-stage startup" signal is worded
     completely differently on LinkedIn ("Co-founder", "MVP", "Summit") than on GitHub
     ("agentic", "WIP", "hackathon") or Reddit ("feedback wanted") — and explicitly instructs the
     model to list every co-founder by name, never concatenate multiple people into one string.
  2. **Extract** — a cheap, tool-free Chat Completions call with
     `response_format={"type": "json_object"}` that converts the browse step's free-text findings
     into strict JSON matching `schemas.py` (`founder_name` + `co_founders` array + the rest of
     the `RawCandidate` fields).
  Any failure at either step returns an empty result — the calling tool then falls back to its
  next real path or mock data, never raising.
- **`localization.py`** — `localize_terms(terms, geography)`. Maps geography → language, keeps a
  jargon allowlist (SaaS, MVP, co-founder, CEO, API, seed, hackathon, ...) in English, translates
  everything else via one batched OpenAI call — or a small built-in Spanish/Portuguese/German
  dictionary when no key is configured.

**Plan-C fallback candidate**: a hardcoded, always-on safety net, not part of the discovery
pipeline itself — see `src/nodes/pipeline.py::_apply_fallback_candidate` and the diagram's
`[post]` step above. See README §"Plan C — the hardcoded FyTic fallback".

### 2.3 Tools layer — `src/tools/*.py`

Every tool exposes `async def search(query, niche, discovery_pass, filters_context) ->
(list[RawCandidate], list[str])` and follows the same fallback contract: try the best available
real path, fall back to the next, and always fall back to mock data if nothing real is available
or every real path fails (see README §3).

| Source | Priority order |
|---|---|
| `github` | real API (unauthenticated works) → mock |
| `arxiv` | real API (free, keyless) → mock |
| `reddit` | real `reddit.com/search.json` (free, keyless) → OpenAI agent → mock |
| `google` | OpenAI agent → mock |
| `producthunt` | OpenAI agent → mock |
| `youtube` | OpenAI agent → mock |
| `linkedin` | OpenAI agent only (no viable public API) → mock |
| `twitter` | OpenAI agent only (no viable free API) → mock |
| `accelerators` | OpenAI agent only (no unified directory API) → mock |

### 2.4 Data files — `src/data/*.json`

| File | Purpose |
|---|---|
| `filter-options.json` | Dropdown options for niche/geography/channels/stage_signal (advisory — free text is still accepted) |
| `niche-search-profiles.json` | Per-niche prioritized sources, query templates, evidence floor, fallback parent, and the adaptive `questionnaire` block |
| `channel-vocabulary.json` | Per-source typical labels/events/framing/site-hint, driving both query wording and the browse-agent prompt |
| `known-startups.json` | Persistent dedup memory — grows after every run; also the thing to check first if a real result seems to be missing (see README §5) |
| `mock-search-results.json` | Synthetic candidate pool used whenever a source has no real path available |

