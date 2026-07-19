# VC Brain — Orchestration Design & API Reference

This is the technical reference for building a frontend against this backend, and for
understanding how a request actually flows through the system. For setup/run instructions, see
`README.md`.

---

## 1. What this is

A FastAPI service that takes a one-time filter submission and runs a 10-node discovery pipeline
that actively searches the live web (via an OpenAI agentic browsing layer) across multiple
channels — GitHub, Google, LinkedIn, Twitter/X, YouTube, Reddit, Product Hunt, accelerator
directories, arXiv — for early-stage, low-visibility startups/founders matching a niche. It
returns a ranked, deduplicated list, favoring hard-to-find candidates over well-documented ones.

Two endpoints:
- `GET /search/questionnaire` — given a niche (+ stage), returns which optional filter fields are
  actually worth showing in the frontend's form.
- `POST /search` — runs the full pipeline, returns ranked candidates.

---

## 2. Orchestration design

### 2.1 Pipeline overview

```
 SearchFilters (frontend request)
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
 │      direct-match + founder-first + keyword + channel-vocabulary        │
 │      query variants per source (src/data/channel-vocabulary.json)       │
 │      + optional LLM diversification if OPENAI_API_KEY is set            │
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
 RunResult (sorted by discovery_value_score, truncated to max_results)
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

### 2.3 Tools layer — `src/tools/*.py`

Every tool exposes `async def search(query, niche, discovery_pass, filters_context) ->
(list[RawCandidate], list[str])` and follows the same fallback contract: try the best available
real path, fall back to the next, and only ever fall back to mock data if
`GENUINE_RESULTS_ONLY` is not set (see README §3).

| Source | Priority order |
|---|---|
| `github` | real API (unauthenticated works) → mock |
| `arxiv` | real API (free, keyless) → mock |
| `reddit` | real `reddit.com/search.json` (free, keyless) → OpenAI agent → mock |
| `google` | OpenAI agent → Google Custom Search API (if keyed) → mock |
| `producthunt` | OpenAI agent → Product Hunt GraphQL API (if keyed) → mock |
| `youtube` | OpenAI agent → YouTube Data API v3 (if keyed) → mock |
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

---

## 3. Frontend contract

### 3.1 `GET /search/questionnaire`

**Query params:**

| Param | Type | Required |
|---|---|---|
| `niche` | string | yes |
| `stage_signal` | string | no |

**Response:**

```json
{
  "niche": "AI Infra",
  "resolved_via": "exact",
  "always_show": ["niche", "geography", "city", "channels", "stage_signal", "keywords"],
  "recommended_fields": ["target_customer", "team_size_max", "team_size_min", "tech_stack"],
  "suggested_keywords": ["GPU scheduling", "inference", "vector database", "model serving"],
  "trace": ["[02:18:02] Node 2 (niche_adapter): exact profile match for 'AI Infra'"]
}
```

Call this once the user has picked a niche (and stage, if already chosen) to decide which of the
optional fields below to actually render, before submitting the full form to `POST /search`.

### 3.2 `POST /search` — request body

`niche` and `founder_view` are **required**. Everything else is optional.

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `niche` | string | **yes** | — | Free text accepted; fuzzy/substring-matched to the nearest known niche or a generic fallback |
| `founder_view` | boolean | **yes** | — | `false` = one row per startup (co-founders consolidated); `true` = one row per founder (startup repeats across co-founders) |
| `geography` | string \| null | no | `null` | Also drives term localization (§2.2) |
| `city` | string \| null | no | `null` | |
| `channels` | string[] | no | `[]` | Advisory; the pipeline's own source selection is niche/stage-driven |
| `stage_signal` | string \| null | no | `null` | `"Idea"` / `"MVP"` / `"Launched"` / `"Unknown"` — `"Idea"`/`"Unknown"`/unset adds YouTube/Twitter/Reddit |
| `keywords` | string[] | no | `[]` | Always-available free text, localized and folded into every source's queries |
| `founded_after` | integer \| null | no | `null` | Hard filter — only excludes when the candidate's founded year is known |
| `founded_before` | integer \| null | no | `null` | Same as above |
| `has_clients` | boolean \| null | no | `null` | Hard filter — only excludes on a known mismatch |
| `team_size_min` | integer \| null | no | `null` | Hard filter — only excludes on a known mismatch |
| `team_size_max` | integer \| null | no | `null` | Hard filter — only excludes on a known mismatch |
| `business_model` | string \| null | no | `null` | Localized; folded into query text |
| `target_customer` | string \| null | no | `null` | Localized; folded into query text |
| `tech_stack` | string[] | no | `[]` | Localized; folded into query text |
| `funding_stage_filter` | string \| null | no | `null` | `"bootstrapped"` / `"pre-seed"` / `"seed"` — hard filter, only excludes on a known mismatch |
| `max_results` | integer | no | `10` | Bounded 1–15 |

**Minimal valid request:**

```json
{ "niche": "AI Infra", "founder_view": false }
```

### 3.3 `POST /search` — response body

```
RunResult
├── run: RunMeta
│   ├── niche: string                 — echoes the input niche string as submitted
│   ├── run_date: string (ISO date)
│   ├── passes_executed: integer      — 1 or 2 (Section 7 adaptive broadening/narrowing)
│   └── founder_view: boolean         — echoes which view mode produced these results
└── results: Candidate[]              — sorted by discovery_value_score, length ≤ max_results
```

**`Candidate` fields:**

| Group | Field | Type |
|---|---|---|
| Identity | `founder_name` | string — the primary founder for this row |
| | `co_founders` | string[] — any other named founders, never merged into `founder_name` |
| | `founder_city` / `founder_country` | string \| null |
| | `founder_linkedin` | string \| null |
| | `founder_education` | string \| null |
| | `founder_prior_ventures` | string[] |
| | `startup_name` | string |
| | `website` | string \| null |
| | `domain_registered_date` | string \| null |
| | `estimated_founded_year` | integer \| null |
| Product & stage | `niche` | string — the niche this candidate was actually matched against |
| | `one_line_description` | string |
| | `product_stage` | `"idea"` \| `"mvp"` \| `"launched"` \| `"unknown"` |
| | `team_size_estimate` | integer \| null |
| | `tech_stack_signals` | string[] |
| | `has_clients` | boolean \| null |
| Traction | `traction_signals.github_repo_url` | string \| null |
| | `traction_signals.github_commit_activity` | string \| null |
| | `traction_signals.linkedin_followers` | integer \| null |
| | `traction_signals.twitter_followers` | integer \| null |
| | `traction_signals.press_mentions` | string[] |
| | `traction_signals.job_postings_found` | string[] |
| Funding | `funding_status` | `"bootstrapped"` \| `"pre-seed"` \| `"seed"` \| `"unknown"` |
| | `funding_amount_estimate` | string \| null |
| | `investors_mentioned` | string[] |
| Discovery process | `source_channel` | string |
| | `search_queries_used` | string[] |
| | `discovery_signals` | string[] |
| | `discovery_pass` | integer |
| Dedup (Node 6) | `dedup_status` | `"genuinely_new"` \| `"possible_duplicate"` |
| | `possible_duplicate_of` | string \| null |
| | `dedup_signals_matched` | string[] |
| Scoring (Node 7) | `discovery_value_score` | number, 0–100 |
| | `discovery_value_reasoning` | string |
| Trust | `confidence` | `"low"` \| `"medium"` \| `"high"` |
| | `confidence_reasoning` | string |
| | `evidence` | `{source_url, snippet, date_captured}[]` |
| | `red_flags` | string[] |
| | `agent_trace` | string[] — full ordered log of every query/decision behind this result |
| | `recommended_next_step` | string |
| | `date_found` | string (ISO date) |
| | `status` | `"new_lead"` \| `"needs_verification"` \| `"activated"` |

### 3.4 Full example response

`founder_view: false` — one row per startup, two co-founders consolidated into one entry:

```json
{
  "run": {
    "niche": "Mexican LegalTech",
    "run_date": "2026-07-18",
    "passes_executed": 1,
    "founder_view": false
  },
  "results": [
    {
      "founder_name": "Eduardo Llaguno Velasco",
      "co_founders": ["Frida Velázquez Esquer"],
      "founder_city": null,
      "founder_country": "Mexico",
      "founder_linkedin": null,
      "founder_education": null,
      "founder_prior_ventures": [],
      "startup_name": "Iurefficient",
      "website": "https://www.iurefficient.com",
      "domain_registered_date": null,
      "estimated_founded_year": 2026,
      "niche": "Mexican LegalTech",
      "one_line_description": "Plataforma que centraliza la gestión de casos, análisis de documentos y comunicación con clientes mediante inteligencia artificial.",
      "product_stage": "launched",
      "team_size_estimate": null,
      "tech_stack_signals": [],
      "has_clients": null,
      "traction_signals": {
        "github_repo_url": null,
        "github_commit_activity": null,
        "linkedin_followers": null,
        "twitter_followers": null,
        "press_mentions": [],
        "job_postings_found": []
      },
      "funding_status": "unknown",
      "funding_amount_estimate": null,
      "investors_mentioned": [],
      "source_channel": "Google search",
      "search_queries_used": ["software para abogados gestor de expedientes jurídicos Mexico"],
      "discovery_signals": ["Small, recently active site with no press coverage"],
      "discovery_pass": 1,
      "dedup_status": "genuinely_new",
      "possible_duplicate_of": null,
      "dedup_signals_matched": [],
      "discovery_value_score": 71.4,
      "discovery_value_reasoning": "Little to no press/follower presence — strong cold-start signal; recently registered domain; no confirmed vc backing found.",
      "confidence": "medium",
      "confidence_reasoning": "At least one concrete artifact confirms this candidate exists, but corroboration is limited.",
      "evidence": [
        {
          "source_url": "https://www.iurefficient.com",
          "snippet": "Plataforma de gestión legal con inteligencia artificial para despachos.",
          "date_captured": "2026-07-18"
        }
      ],
      "red_flags": [],
      "agent_trace": [
        "[02:18:02] Node 1 (filter_intake): received niche='Mexican LegalTech'",
        "[02:18:02] Node 2 (niche_adapter): exact profile match for 'Mexican LegalTech'",
        "[02:18:02] Localized terms to Spanish via OpenAI: ['Law Firms'] -> ['despachos legales']",
        "[02:18:03] [google] OpenAI research agent extracted 1 candidate(s)",
        "[02:18:03] Consolidated 2 results for 'Iurefficient' into one row — founders: ['Eduardo Llaguno Velasco', 'Frida Velázquez Esquer']",
        "[02:18:03] Node 9 (confidence_flagging): 'Iurefficient' -> confidence=medium, red_flags=0"
      ],
      "recommended_next_step": "Needs light verification (confirm team/product details) before outreach.",
      "date_found": "2026-07-18",
      "status": "new_lead"
    }
  ]
}
```

With `"founder_view": true` on the same underlying find, this single row would instead be
returned as **two** rows — `founder_name: "Eduardo Llaguno Velasco"` with
`co_founders: ["Frida Velázquez Esquer"]`, and `founder_name: "Frida Velázquez Esquer"` with
`co_founders: ["Eduardo Llaguno Velasco"]` — everything else identical.
