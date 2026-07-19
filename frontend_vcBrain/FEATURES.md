# VC Brain — Features

VC Brain is a frontend-only mockup of an internal VC investor tool. There is no backend, no
database, and no real API — every number, name, and log entry lives in the JSON files under
`/data` and is loaded straight into the page. The point of the mockup is the **workflow and the
interface**: source → screen → fact-check → decide, all guided by a thesis you set yourself, with
nothing shown until you ask for it.

This document lists every section and every feature currently in the app. Nothing is left out.

---

## App-wide features

- **Light mode by default.** The app never follows your OS dark-mode setting automatically. It
  always starts in light mode; dark mode is only ever turned on if you click the toggle.
- **Light/dark toggle.** A button in the top-right of the top bar switches themes instantly and
  remembers your choice the next time you open the app (saved in your browser).
- **A custom, hand-drawn icon set.** No emoji, no off-the-shelf icon library — every icon in the
  app (sidebar navigation, empty states, search prompts, the two decision panels) is a small
  original line-drawing built specifically for this app, rendered inline as SVG.
- **Sidebar navigation with plain names.** Nine sections, each with a friendly one-word or
  two-word name, always visible on the left: Overview, My Focus, Discover, Founders, Scorecard,
  Fact Check, Checklist, Report, and Decision.
- **Nothing shows until you ask.** Every section that lists or analyzes data opens with a guided
  prompt instead of dumping a table on you. You either fill in a short search (Overview, Discover,
  Founders) or pick a startup from a search/browse list (Scorecard, Fact Check, Checklist, Report,
  Decision). The one exception is **My Focus**, which is itself the "tell us what you want" screen,
  so it has nothing to gate.
- **Compound, multi-attribute search — not just keyword matching.** Every guided search has a
  free-text box, but typing in it does more than substring-match: an "Understand my search" (or
  "type it in your own words," on My Focus) tool reads one sentence — e.g. *"technical founder,
  Berlin, AI infra, seed stage, top-tier accelerator"* — and pulls out every filter it can
  recognize **at once**: industry, stage, geography (down to specific cities, not just broad
  regions), which research channel to source from, and founder traits. It shows you exactly what
  it picked up on as chips, then applies all of it to the structured filters in one action —
  instead of making you click through five separate filter chips by hand. Plain keyword matching
  against names/bios/descriptions still runs alongside it as a fallback for anything the parser
  didn't recognize.
- **"Where should we look?" research-channel filtering.** Startups and founders can be filtered by
  how they were originally found: GitHub, Google / web search, academic papers, accelerators,
  hackathons, community/conferences, warm intro, or direct application. This isn't cosmetic — every
  startup in the mock data is actually linked back to a real entry in the sourcing feed, so
  filtering by "GitHub" on the Founders page, for example, really does only show founders whose
  current company was found on GitHub.
- **No single blended score, anywhere.** This is a hard rule the whole app follows, not just the
  Scorecard page: nothing is ever averaged across independent axes and presented as one number.
  Overview ranks by fit with your stated focus (not a fabricated composite score) and shows the
  three Scorecard axes side by side, un-combined. Fact Check has no page-level confidence number —
  only a distribution across individual claims. Founders carry exactly one persistent number (the
  Founder Score), not a breakdown into invented sub-traits.
- **Design system.** No card-grid or boxed-shadow tiles anywhere — data is shown as dense lists,
  ranked tables, split-panels (list + detail), timelines, and inline expandable rows. Visually the
  app leans toward a clean, rounded, soft-shadowed look: big pill-shaped buttons, generous
  whitespace, a blue accent color, and grouped-list-style tables — while keeping data dense and
  scannable rather than spread across oversized tiles. Every color, spacing value, corner radius,
  shadow, and transition in the app comes from one shared set of design tokens, so light and dark
  mode stay consistent everywhere at once.

---

## Overview (`/`)

The main landing page — every startup you're tracking, ranked by how well it fits what you're
looking for.

- **Guided search panel** ("What kind of startups do you want to see?") with:
  - Free-text keyword box, plus the "Understand my search" compound-query tool described above
  - Industry (multi-select)
  - Stage — how early or late (multi-select)
  - Geography, grouped by country (multi-select)
  - Momentum — getting better / staying steady / getting worse (multi-select)
  - How much they're raising, as a min–max dollar range
  - "Where should we look?" research-channel filter
  - A single "Show me the list" button — nothing appears until you click it
- Once run, the panel collapses into a one-line summary with a "Change my search" button to
  reopen it.
- **At-a-glance numbers strip**: how many results, how many are in diligence, how many are at
  decision, average fit with your focus, how many are trending up — computed from your filtered
  results, not the whole dataset.
- **Ranked list** — every matching startup, **ranked by fit with your stated focus** (never by an
  averaged or invented "overall score"), showing: rank, name + founder names, industry/stage,
  current status (Sourcing → Screening → Diligence → Memo → Decision → Invested/Passed), fit with
  your focus (as a bar), the **three Scorecard axes shown independently side by side** (People /
  Market / Idea — never blended into one number, even in this compact list view), a 6-month
  momentum sparkline with trend arrow, how much they're raising, and last activity date. Click any
  row to jump straight into its Scorecard.

## My Focus (`/thesis`)

Where you tell VC Brain what you actually want to see everywhere else in the app.

- **Plain-English explainer** at the top of the page and a short intro line before you touch
  anything, so it's clear what this screen does and why it matters.
- **Ready-made starting points** (a simple list on the left) — four saved searches (e.g.
  "AI-Native Infrastructure," "Climate & Resource Systems") each with a one-line description and a
  simple risk badge (Careful / Balanced / Bold). Click one to load it into the editor.
- **Editable form** (on the right) with plain-language questions instead of form-field jargon:
  - "What industries are you into?" — chip multi-select
  - "How early or late-stage?" — chip multi-select
  - "Where in the world?" — chip multi-select
  - "Smallest / largest check you'd write" — in $K, not raw dollars
  - "How big a slice of the company?" — ownership %, plain percent input
  - "How much risk feels okay?" — Careful / Balanced / Bold dropdown, with a one-line description
    of what each means
  - A **live plain-English summary sentence** at the top of the form that rewrites itself as you
    change anything — e.g. *"You want AI Infrastructure and Developer Tools startups, at the
    Pre-seed and Seed stage, in North America and Europe. You'd write checks between $50K and
    $150K, aiming to own about 3% of the company, and you're balanced about risk."*
  - "Start over from this preset" and "Save my choices" buttons (a demo note reminds you nothing
    actually leaves your screen — this is a mockup, not a live system).
- **"Or just type it in your own words"** — the compound multi-attribute query tool described in
  the app-wide features above, tuned to this page's context. Type a whole sentence stacking as
  many details as you want, and see it resolved into industries, stage, geography (cities,
  countries, or broad regions), research channels, and founder traits all at once, plus a "how
  sure are we" confidence meter. If nothing matches, it says so plainly and suggests what kind of
  words to try. A row of clickable example phrases is provided to try the feature instantly.

## Discover (`/sourcing`)

New startups — the ones that applied to you, and the ones found on your behalf.

- **Guided search panel** ("What kind of new startups do you want to find?") with:
  - Free-text keyword box, plus the "Understand my search" compound-query tool
  - "How did we hear about them?" — they applied to us / we found them (multi-select)
  - "Where things stand" — just found / looking into it / became an application / passed on
  - "Where should we look?" — the full research-channel filter (GitHub, Google, academic papers,
    accelerators, hackathons, community, etc.)
  - "Find startups" button — nothing shows until you click it
- **Merged feed**, most recent first, combining direct applications and system-discovered leads in
  one dense table: how they were found, date, startup + founder names, channel, a plain-English
  summary, and current status. Any lead that turned into a real application is called out inline
  with the date it happened.
- **"Where we look" — channel intelligence table**: every research channel the fund uses (GitHub
  trending, HackNation, arXiv alerts, two named accelerators, maintainer outreach, a conference,
  and Google search), each with how many active deals it's produced, total startups sourced,
  conversion rate, a quality score bar, and when it last surfaced something — filterable by the
  same research-channel selection as the feed above.

## Founders (`/founders`)

A directory of people, not companies. The Founder Score is a single number that lives with the
person — it persists across whatever company they're building next, and it is deliberately kept
separate from the per-opportunity Founder axis that lives on a startup's Scorecard.

- **Guided search panel** ("What kind of founders do you want to see?") with:
  - Free-text keyword box, plus the "Understand my search" compound-query tool (recognizes traits
    like "technical," "domain-expert," "first-time," or "repeat" directly from a typed sentence)
  - "What kind of founder?" — archetype multi-select, built dynamically from the data
  - "First time, or done this before?" — first-time founders vs. repeat founders
  - "Where" — geography, grouped by country
  - "How good, at minimum?" — a 0–100 score floor
  - "Where should we look?" — research-channel filter, applied to the founder's *current* company
  - "Show founders" button — nothing shows until you click it
- **Master-detail layout**: a ranked list on the left (rank, initials monogram, name, founder type,
  score bar, trend arrow, a "First-time" badge where relevant); clicking a row opens the full
  profile on the right.
- **Founder profile** includes: name, location, founder type, the single persistent Founder Score
  with its trend (labeled as following the person, not the company), a short bio, a full list of
  prior ventures (name, role, outcome, years — or a friendly "this is their first company" message
  if there are none), and a **visual timeline** of everything that's happened in their career,
  oldest to newest. There is no invented sub-score breakdown here — Founder Score is one number,
  on purpose.

## Scorecard (`/screening`)

For one selected startup: how the people, the market, and the idea each score — kept completely
separate on purpose.

- **Pick a startup** first (search or browse by name/industry/stage/location/tags); nothing shows
  until you choose one.
- Once picked, a switcher lets you jump to a different startup at any time without leaving the
  page.
- **Three independent columns** — "The People," "The Market," and "Does the Idea Fit?" — each with
  its own score, its own trend arrow, its own color, its own bar, and its own short written
  reasoning. These numbers are **never averaged or combined** into one overall score anywhere on
  this page or anywhere else in the app; that's the entire point of the screen, and Overview's
  ranked list respects it too.
- **A 5-month trend chart** plotting all three scores over time on one shared graph, with a
  color-coded legend, so you can see whether the people, the market, or the idea has been moving
  in the right direction lately.

## Fact Check (`/trust`)

For one selected startup: everything they've claimed, where it came from, and how sure the fund is
it's actually true — **checked claim by claim, never rolled up into one company-level trust
score.**

- **Pick a startup** first, same guided picker as Scorecard; nothing shows until you choose one.
- **Claim-by-claim list**, each one an expandable row:
  - Collapsed: the claim itself, a confidence meter, and — if something doesn't add up — a bright
    red "Contradiction flagged" badge, visible without even opening the row.
  - Expanded: where the claim came from, what kind of proof it is, when it was last checked, and —
    if flagged — the full text of what contradicts it, called out in a distinct red block.
  - Rows with a contradiction get a subtle red tint even before you open them, so nothing gets
    lost by accident.
- **A distribution rollup, not a single score**: right above the claim list, a plain-text count —
  how many claims are contradicted out of the total, and how many fall into each confidence tier
  (high / medium / low). This is deliberately a *count across claims*, not an average — there is
  no single "trust score" for the company anywhere on this page.

## Checklist (`/diligence`)

For one selected startup: a running log of what's been checked and what's still open.

- **Pick a startup** first, same guided picker pattern; nothing shows until you choose one.
- A summary line up top: how many entries are verified, still open, or didn't check out.
- **Search and filter bar**: free-text keyword search plus dropdowns for category (Team, Market,
  Product, Financial, Legal, Technical) and status (verified / open / contradicted).
- Entries are grouped by category, most recent first within each group, and rendered as
  expandable rows — collapsed shows the item and its status/date; expanded shows who's responsible
  and the full notes.

## Report (`/memo`)

For one selected startup: the full write-up, formatted like something you'd actually hand to an
investment committee — but in plain language.

- **Pick a startup** first, same guided picker pattern; nothing shows until you choose one.
- A single scrolling document made of these sections, always shown in this order:
  - **The Basics** — a compact facts strip: name, industry, stage, location, founding year, how
    much they want, how much we'd put in
  - **In a Nutshell** — the required narrative snapshot as an actual written paragraph (not a
    table): the structural problem, how the product solves it, and — only when the data is
    actually available — how big the opportunity is and why the timing matters now
  - **Why This Could Work** — the investment case, as a short numbered list
  - **The Good, the Bad & the Risks** — a four-quadrant strengths / weaknesses / opportunities /
    threats breakdown
  - **Problem & Product** — what's broken, and what they built to fix it, in more detail
  - **How It's Doing So Far** — key numbers/traction, each with a date
  - **The Team** *(shown only if we have it — otherwise a clear "not disclosed" or "unavailable at
    this stage" message, never a blank space)*
  - **The Tech, and Why It's Hard to Copy** *(same fallback rule)*
  - **How Big Is the Market?** *(plain-language TAM/SAM/SOM — "everyone who could ever buy this,"
    "the slice we could realistically sell to," "what we could actually capture" — same fallback
    rule)*
  - **Who Else Is Doing This?** *(competitor table, same fallback rule)*
  - **What We've Checked** *(a rollup of the Checklist page's numbers, same fallback rule)*
  - **Money & Round Structure**, **Who Owns What**, and **How This Could End** — three genuinely
    separate sections (not folded into one umbrella block), each individually flagged as "not
    always shared" and each with its own independent missing-data fallback. "How This Could End"
    names the actual plausible exit paths (which category of acquirer, or a private-equity
    roll-up) and explains *why* that buyer would pay a premium, wherever the data is available —
    not just a one-line gloss. **Nothing is ever fabricated or left blank** — every missing field
    says so explicitly.

## Decision (`/decision`)

For one selected startup: should we write the check?

- **Pick a startup** first, same guided picker pattern; nothing shows until you choose one.
- **The headline call**, always visible at the top: Invest / Pass / Watch (color-coded), how much
  we'd invest, the reasoning in plain language, and whether a decision has actually been made yet
  (or is still pending — never a fabricated date).
- Two **clearly separate panels**, side by side, that are deliberately never blended into one
  opinion:
  - **The Case Against It** — the strongest argument for *not* doing this deal, the biggest
    risks, and what would need to change for the fund's mind to change.
  - **Does It Fit What We Already Own?** — which existing portfolio companies overlap with this
    one (or a plain "none" if there's no overlap), how it spreads out the fund's bets, a risk-of-
    overlap meter, and a fit score.

---

## What's simulated vs. real

Everything in this app is a mockup:

- All startups, founders, scores, evidence, logs, memos, and sourcing signals live in static JSON
  files under `/data` and never change based on anything you do.
- "Saving" a focus, applying filters, or toggling a decision does not persist anywhere or affect
  what any other page shows — every screen is self-contained.
- The compound-query tool ("Understand my search" / "type it in your own words") is a small,
  local keyword-and-pattern matcher, not a real language model — it recognizes phrases it's been
  taught to recognize (industries, stages, known cities/countries/regions, sourcing-channel words,
  a handful of founder-trait words) and is upfront when it can't figure something out, rather than
  guessing.
- The "research channels" (GitHub, Google, accelerators, etc.) are pre-baked links between mock
  startups and mock sourcing-feed entries, not live integrations.
- There is no login, no real user, and no backend of any kind — this is a frontend-only
  demonstration of the product experience.
