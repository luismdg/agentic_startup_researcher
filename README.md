# VC Brain — Agentic Startup Sourcing

A FastAPI service that runs the 10-node discovery pipeline described in the architecture doc:
it takes a one-time, adaptive filter submission (niche, geography, city, stage, and a bunch of
optional richer attributes) and returns a ranked list of up to `max_results` candidate
founders/startups across multiple channels, favoring low-visibility, hard-to-find candidates
over well-documented ones. With `OPENAI_API_KEY` set, most of those channels are researched by
an actual agentic web-browsing loop (src/orchestration/), not simple REST calls.

This repo actually holds three sibling projects that together form the full product:

| Project | What it is | Port |
|---|---|---|
| `src/` (this one) | The sourcing pipeline documented below — finds candidates | `8000` |
| `reasoning-engine/` | Scores/memos each candidate against an investor thesis (3-axis LLM scoring, investment memos) | `8001` |
| `frontend_vcBrain/` | The Next.js UI — works standalone on static mock data, or live against the two backends above | `3000` |

Sections 1-5 below cover this backend in isolation (its own setup, API, mock/real mode, tests).
**Jump to [Section 6](#6-running-the-full-stack-sourcing--reasoning-engine--frontend_vcbrain) if
you want all three running together, feeding the frontend.**

## 1. Setup

No virtual environment needed — install straight into your existing Python (conda base, or
plain system Python):

```powershell
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your OpenAI API key — this is the headline one, see
[Mock mode vs. real mode](#3-mock-mode-vs-real-mode):

```powershell
copy .env.example .env
```

```
OPENAI_API_KEY=sk-...
```

## 2. Run it

```powershell
uvicorn src.main:app --reload
```

The API is now at `http://127.0.0.1:8000`. Interactive docs (Swagger UI) are at
`http://127.0.0.1:8000/docs` — the easiest way to try requests by hand.

### Step 1 (optional but recommended): check the adaptive questionnaire

`GET /search/questionnaire?niche=...&stage_signal=...` tells you which of the richer optional
attributes are actually worth filling in for that niche/stage combo, plus a few suggested
keywords — the form adapts instead of showing every field for every search.

```bash
curl "http://127.0.0.1:8000/search/questionnaire?niche=AI%20Infra&stage_signal=MVP"
```

```json
{
  "niche": "AI Infra",
  "resolved_via": "exact",
  "always_show": ["niche", "geography", "city", "channels", "stage_signal", "keywords"],
  "recommended_fields": ["target_customer", "team_size_max", "team_size_min", "tech_stack"],
  "suggested_keywords": ["GPU scheduling", "inference", "vector database", "model serving"]
}
```

### Step 2: search

`POST /search` with a JSON body. `niche` and `founder_view` are required — everything else is
optional:

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

**`founder_view` (required boolean) — one row per founder, or one row per startup:**
- `false` (startup-centric): one row per unique startup. If a startup has multiple co-founders,
  they're all listed together in that single row's `co_founders` array — the startup never
  appears more than once.
- `true` (founder-centric): one row per named founder. A startup with 3 co-founders legitimately
  produces 3 rows — one per founder — each row's `co_founders` listing the others for context.

Internally, results are always consolidated to one row per startup first (so two search hits
that found the same startup via two different co-founders' names correctly merge into one
company with both founders listed, rather than looking like two different startups) — 
`founder_view: true` then explodes that back out per founder. `run.founder_view` in the response
echoes which mode produced it.

Valid values for `niche`/`geography`/`channels`/`stage_signal` live in
`src/data/filter-options.json` — you can also submit free text (e.g. a niche not in that list);
Node 2 will fuzzy-match it to the nearest known niche or fall back to a generic profile rather
than failing. `keywords` is always available as a free-text escape hatch on top of every other
filter — nothing here is a rigid enum.

**curl:**

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"niche":"AI Infra","founder_view":false,"geography":"United States","max_results":10}'
```

**PowerShell:**

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/search `
  -ContentType "application/json" `
  -Body '{"niche":"AI Infra","founder_view":false,"geography":"United States","max_results":10}' | ConvertTo-Json -Depth 10
```

The response matches the Section 8 schema: `run` (niche, run date, passes executed, founder_view)
plus `results` — up to `max_results` candidates (default 10), each with identity (including
`co_founders`), traction, funding, `has_clients`, dedup status, `discovery_value_score` +
reasoning, confidence, red flags, and a full `agent_trace` log of every query and decision that
produced it.

## 3. Mock mode vs. real mode

Every source works with **zero configuration** by reading from synthetic data in
`src/data/mock-search-results.json`. `OPENAI_API_KEY` is the one key that matters most: when set,
it upgrades every channel except the already-free GitHub/arXiv/Reddit to **real agentic web
browsing** — the model actually searches the live web (via OpenAI's hosted web-search tool) and
extracts structured candidates from what it finds, per channel:

| Source | Real path | Without a key |
|---|---|---|
| GitHub | nothing needed (public API works unauthenticated) | still attempts a real call; falls back to mock only if it fails |
| arXiv | nothing needed (free, keyless) | always real |
| Reddit | nothing needed (`reddit.com/search.json` is free/keyless), `OPENAI_API_KEY` as a fallback path | mock |
| Google | `OPENAI_API_KEY` (agentic browsing) | mock |
| LinkedIn | `OPENAI_API_KEY` (agentic browsing of public linkedin.com pages) | mock |
| Twitter/X | `OPENAI_API_KEY` (agentic browsing — no viable free API exists anymore) | mock |
| YouTube | `OPENAI_API_KEY` (agentic browsing) | mock |
| Product Hunt | `OPENAI_API_KEY` (agentic browsing) | mock |
| Accelerators | `OPENAI_API_KEY` (agentic browsing of cohort/directory pages) | mock |

Every real path fails safe: a bad/missing tool, a network error, malformed output — anything —
falls back to mock data for that call, logged in `agent_trace`, rather than erroring out the
whole search.

**Each channel is searched in its own vocabulary**, not one generic phrasing everywhere — people
signal "early-stage startup" completely differently per platform (a LinkedIn headline says
"Co-founder"/"MVP"/"Summit"; a GitHub repo says "agentic"/"WIP"/"hackathon"; a Reddit post says
"feedback wanted"; YouTube/Twitter idea-stage founders say "building in public"). This mapping
lives in `src/data/channel-vocabulary.json` and drives both Node 3's query wording and the
OpenAI web-research agent's browsing prompt — edit that file to tune or extend it per channel.

**YouTube/Twitter/Reddit are folded in automatically for idea-stage searches** — set
`"stage_signal": "Idea"` (or leave it unset/`"Unknown"`) and the pipeline adds these three on top
of whatever the niche normally prioritizes, since that's where founders post before any company
site, repo, or LinkedIn page exists. `"MVP"`/`"Launched"` stick to the niche's configured sources.

**Business terms are localized to the search geography, but startup jargon isn't** —
`business_model`, `target_customer`, `keywords`, and `tech_stack` get translated into the local
language of `geography` before being turned into queries (e.g. `"target_customer": "Law Firms"`
becomes `"despachos legales"` when `geography` is `"Mexico"`), while recognized global
startup/tech jargon (`SaaS`, `MVP`, `co-founder`, `CEO`, `API`, `seed`, `hackathon`, ...) is left
in English, since that's what people actually search with everywhere. `OPENAI_API_KEY` makes this
a real translation call (`src/orchestration/localization.py`); without it, a small built-in
dictionary covers this app's own common filter vocabulary for Spanish/Portuguese/German so it
still behaves sensibly with zero configuration. Check `agent_trace` for the `"Localized terms
to..."` line to see exactly what was translated.

`.env` is read automatically on startup (via `python-dotenv`) — set the variable there instead of
your shell if you'd rather not export it every session:

```
OPENAI_API_KEY=sk-...
```

### Plan C — the hardcoded FyTic fallback

Always on, not configurable. If a run's genuine search for the `"Mexican LegalTech"` niche didn't
turn up anything named `"FyTic"`, one hardcoded candidate gets appended to the results as
insurance. It is never treated as a real discovery: `confidence` is forced to `"low"`,
`status` to `"needs_verification"`, `discovery_value_score` to `0`, and `discovery_signals`/
`confidence_reasoning` both say outright that it was manually supplied, not found or verified by
the agent. If a genuine result for FyTic already exists, nothing is added. Edit the hardcoded
details in `src/nodes/pipeline.py::_build_fallback_candidate` if you need to change them.

### If you want to find your own startup for real

You need `OPENAI_API_KEY` — nothing else here can find a real company beyond it:

1. **Get an OpenAI API key** at [platform.openai.com](https://platform.openai.com/api-keys) and
   put it in `.env` as `OPENAI_API_KEY=sk-...` — **never paste the key itself into a chat with
   an AI assistant, including this one; only put it directly in your local `.env` file.** This
   one key unlocks real agentic browsing across Google, LinkedIn, Twitter/X, YouTube, Product
   Hunt, and Accelerators.
2. **GitHub and Reddit already work with zero keys** — both hit free, unauthenticated public
   APIs. If your startup has a public repo or has been mentioned on Reddit, these alone might
   find it.
3. Restart `uvicorn` after editing `.env` so it picks up the new key.
4. Check `GET /search/questionnaire` for your niche + stage, then submit `POST /search` with a
   niche close to your startup's actual space and any keywords/city/tech_stack that narrow it
   down.

#### Worked example: searching for a real, low-visibility, unfunded startup

This is a filter-crafting example, not a scoring change — nothing here is FyTic-specific in the
code, and it shouldn't be. The discovery-value formula (Section 6b) treats every candidate the
same regardless of what you search for; what actually changes your odds of finding a genuinely
obscure startup is **how well your filters match the language that startup actually uses**, not
the category name you'd use to describe it to an investor.

The most common way a real, thinly-documented startup gets missed: its own content may never
literally say the niche name. A 3-post-old LinkedIn presence with a title like "Co-founder at
[Startup]" won't say "LegalTech" anywhere — but it *will* use the product-level language its
target customers actually search with. That's what `keywords`/`business_model`/`target_customer`
are for: they get localized to the search geography's language (Section 3 above) and folded
directly into the literal query text (Node 3), so the search matches real phrasing instead of an
abstract category label.

For a pre-seed, unfunded, Mexico-based LegalTech SaaS with minimal public content, a request
built from its own realistic product/SEO vocabulary — not from guessing at buzzwords — looks
like this:

```json
{
  "niche": "Mexican LegalTech",
  "founder_view": false,
  "geography": "Mexico",
  "channels": ["Google", "LinkedIn"],
  "stage_signal": "MVP",
  "keywords": [
    "software para abogados",
    "gestor de expedientes jurídicos",
    "sistema para despachos de abogados",
    "redacción de contratos con inteligencia artificial",
    "investigación jurídica con inteligencia artificial"
  ],
  "business_model": "SaaS",
  "target_customer": "law firms",
  "funding_stage_filter": "bootstrapped",
  "max_results": 10
}
```

Why each piece matters here, specifically:
- **`keywords`** are the actual Spanish product-language a Mexican legal-tech SaaS would use in
  its own site/posts (case management, document drafting, AI legal research) — not the English
  category label. This is the single biggest lever for finding something whose content never
  says the niche name outright.
- **`niche: "Mexican LegalTech"`** still matters even so — it drives which *sources* get
  prioritized and which channel vocabulary gets used (Section on channel vocabulary above), it
  doesn't require the target's content to literally contain the word.
- **`business_model: "SaaS"`** stays in English (global jargon, never translated) while
  **`target_customer: "law firms"`** gets localized to `"despachos legales"` automatically —
  exactly the term real Spanish-language content would use.
- **`funding_stage_filter: "bootstrapped"`** reflects "no funding, no awards" honestly — and
  since `_apply_user_filters` only ever excludes a candidate when its funding status is *known*
  and *conflicts*, this never risks dropping a real candidate just because funding data wasn't
  found (which is the common case for a genuinely unfunded startup).
- **Nothing here guesses at team size, founding year, or has_clients** — over-constraining with
  assumed values is the fastest way to accidentally filter out the very candidate you're looking
  for.

This is a template for approaching *any* low-visibility startup, not a lookup table — swap in the
real product vocabulary, geography, and constraints for whatever you're actually searching for.

Check each result's `agent_trace` field to see exactly which queries ran and which source (real
vs. mock) produced each candidate — every result is traceable back to its source. If a channel
falls back to mock unexpectedly, the trace will say why (e.g. the web-search tool name didn't
match your API version, or a network error).

## 4. Run the test suite

```powershell
pytest tests/ -v
```

Runs fully offline/deterministic (every tool forced into mock mode in tests regardless of what's
in your `.env`, and dedup runs against a fixed snapshot rather than the real, growing
`known-startups.json`). Verifies the full pipeline end-to-end, the schema, the questionnaire
endpoint, `max_results` truncation, the `has_clients` filter, the dedup + inverted-scoring logic
(a bare-repo, zero-visibility mock candidate must outrank a launched, Product-Hunt-covered one —
the spec's own worked example), that idea-stage searches actually pull in Reddit/Twitter/YouTube
candidates, that query wording differs per channel's vocabulary, the always-on FyTic plan-C
fallback, and `founder_view`'s consolidate/explode behavior (multiple co-founders of the same
startup found separately must merge into one row, never get concatenated into a single
`founder_name` string, and only repeat as separate rows when `founder_view: true`).

## 5. Notes

- Genuinely new, medium/high-confidence results get appended to `src/data/known-startups.json`
  after each run, so future runs dedup against everything you've already found — this file will
  grow as you use the tool. Delete entries from it manually if you want to reset that memory.
- **If a real startup you know exists never appears in results**, before assuming the search is
  broken, check whether it (or a name/domain close to it) is already sitting in
  `known-startups.json`. Node 6 will match a fresh find against that memory on domain/name/founder
  and either drop it as a duplicate or flag it `possible_duplicate` — correct behavior for
  avoiding re-surfacing something already found, but it also means a stale or coincidentally
  similarly-named entry can silently suppress a real one. Worth a quick grep before debugging
  anything else.
- The richer attributes (`founded_after`/`founded_before`, `has_clients`, `team_size_min/max`,
  `funding_stage_filter`) only ever drop a candidate when *both* the filter is set *and* the
  candidate's value is actually known — sparse cold-start data is never penalized just for being
  incomplete.
- Never commit or share your `.env` file — it holds your real API keys.

## 6. Running the full stack (sourcing + reasoning-engine + frontend_vcBrain)

Three separate processes, each in its own terminal. None of them need a `.venv` — install
straight into your conda **base** environment (or plain system Python) for both Python services,
same as Section 1.

### Terminal 1 — sourcing backend (this repo, port 8000)

```powershell
pip install -r requirements.txt
copy .env.example .env   # then add OPENAI_API_KEY — see Section 1
uvicorn src.main:app --reload
```

### Terminal 2 — reasoning-engine (port 8001)

```powershell
cd reasoning-engine
pip install -r requirements.txt
copy .env.example .env   # then add OPENAI_API_KEY (LLM_PROVIDER=openai is the default)
uvicorn app.main:app --reload --port 8001
```

Its `requirements.txt` overlaps almost entirely with this backend's (fastapi, uvicorn, pydantic,
httpx, python-dotenv, openai) — if you've already `pip install`-ed Section 1's requirements into
the same Python, this step usually has nothing left to do. `anthropic` is only imported if you
set `LLM_PROVIDER=anthropic`; leave it as `openai` (the default) and you don't need that package
at all.

### Terminal 3 — frontend_vcBrain (port 3000)

```powershell
cd frontend_vcBrain
npm install
npm run dev
```

Open `http://localhost:3000`.

### How the frontend uses both backends

The frontend never needs either backend running — it ships with static mock data
(`frontend_vcBrain/data/*.json`, read via `lib/data.ts`) so the whole UI works with zero setup.
On top of that, every page also fetches live data from reasoning-engine on each request
(`lib/liveApi.ts`, defaulting to `http://127.0.0.1:8001`, overridable via the `REASONING_API_URL`
env var) and merges it in: live-sourced startups are shown first, mock entries fill in the rest,
and a live entry never duplicates a mock one that shares an id. If reasoning-engine isn't running,
every live fetch fails safe to "no live data" and you just see the mock set — never a broken page.

**Getting a real candidate from the sourcing backend to actually show up on the frontend** is a
manual hop today (nothing auto-connects port 8000 to port 8001): run a search against this
backend, then POST that response to reasoning-engine's ingest endpoint. The two schemas were
reconciled field-for-field, with exactly one difference — this backend's response wraps its run
metadata as `"run"`, reasoning-engine's ingest endpoint expects the same object under `"query"`.

```powershell
$search = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/search `
  -ContentType "application/json" `
  -Body '{"niche":"Mexican LegalTech","founder_view":false,"geography":"Mexico","max_results":10}'

$payload = @{ query = $search.run; results = $search.results } | ConvertTo-Json -Depth 20

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/api/sourcing/ingest `
  -ContentType "application/json" -Body $payload
```

Refresh the frontend — the ingested startup(s) now appear on Overview/Screening/Trust/Memo,
scored and memo'd against reasoning-engine's demo thesis. Ingested results live in
reasoning-engine's process memory only (see `app/api_routes.py`'s `_pipeline_cache`) — restarting
that service clears them and you'll need to re-ingest.

- Never commit or share `reasoning-engine/.env` either — same rule as this backend's `.env`.
- `reasoning-engine`'s own README-equivalent detail (its internal pipeline, schema-reconciliation
  notes, provider switch) lives in its module docstrings — see `app/main.py`, `app/models.py`,
  `app/services/sourcing_adapter.py`, `app/services/llm_client.py`.

**Troubleshooting: `/api/sourcing/ingest` returns 500.** Unlike this backend's `/search` (which
always falls back to mock data on any real-path failure — Section 3), reasoning-engine's scoring
and memo calls are *not* fail-safe: a bad key or a network/TLS failure raises and the ingest
request fails outright rather than degrading. Check `reasoning-engine`'s own terminal output for
the traceback. If it ends in an SSL/certificate error (common behind a corporate proxy or AV
HTTPS-scanning tool), see `RELAX_TLS_STRICT_X509` in `reasoning-engine/app/services/llm_client.py`.
To develop against the full stack with zero API calls/cost while you sort that out, set
`LLM_PROVIDER=fake` in `reasoning-engine/.env` — it returns canned-but-schema-valid scores/memos
so ingest, and everything downstream on the frontend, works fully offline.
