# VC Brain — API Reference

The request/response contract for building a frontend against this backend: what JSON to send,
what JSON you get back. For how the backend actually produces that response, see
`ORCHESTRATION.md`. For setup/run instructions, see `README.md`.

Two endpoints:
- `GET /search/questionnaire` — given a niche (+ stage), returns which optional filter fields are
  actually worth showing in the frontend's form.
- `POST /search` — runs the full pipeline, returns ranked candidates.

---

## 1. `GET /search/questionnaire`

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

---

## 2. `POST /search` — request body

`niche` and `founder_view` are **required**. Everything else is optional.

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `niche` | string | **yes** | — | Free text accepted; fuzzy/substring-matched to the nearest known niche or a generic fallback |
| `founder_view` | boolean | **yes** | — | `false` = one row per startup (co-founders consolidated); `true` = one row per founder (startup repeats across co-founders) |
| `geography` | string \| null | no | `null` | Also drives term localization |
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

**Fuller example:**

```json
{
  "niche": "AI Infra",
  "founder_view": false,
  "geography": "United States",
  "city": "San Francisco",
  "channels": ["GitHub", "Google"],
  "stage_signal": "MVP",
  "keywords": ["GPU scheduling"],
  "has_clients": false,
  "team_size_min": 1,
  "team_size_max": 5,
  "business_model": "open source infra",
  "target_customer": "AI infra teams",
  "tech_stack": ["Rust", "CUDA"],
  "founded_after": 2025,
  "funding_stage_filter": "bootstrapped",
  "max_results": 10
}
```

---

## 3. `POST /search` — response body

```
RunResult
├── run: RunMeta
│   ├── niche: string                 — echoes the input niche string as submitted
│   ├── run_date: string (ISO date)
│   ├── passes_executed: integer      — 1 or 2 (adaptive broadening/narrowing)
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
| Dedup | `dedup_status` | `"genuinely_new"` \| `"possible_duplicate"` |
| | `possible_duplicate_of` | string \| null |
| | `dedup_signals_matched` | string[] |
| Scoring | `discovery_value_score` | number, 0–100 |
| | `discovery_value_reasoning` | string |
| Trust | `confidence` | `"low"` \| `"medium"` \| `"high"` |
| | `confidence_reasoning` | string |
| | `evidence` | `{source_url, snippet, date_captured}[]` |
| | `red_flags` | string[] |
| | `agent_trace` | string[] — full ordered log of every query/decision behind this result |
| | `recommended_next_step` | string |
| | `date_found` | string (ISO date) |
| | `status` | `"new_lead"` \| `"needs_verification"` \| `"activated"` |

---

## 4. Full example response

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
