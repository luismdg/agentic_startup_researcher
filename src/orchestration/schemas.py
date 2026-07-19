"""Shared contract between the browse step and the extract step in
web_research_agent.py. Kept separate from src/models so the orchestration
layer's JSON-facing shape can evolve independently of the pipeline's
internal Pydantic models."""

EXTRACTION_INSTRUCTIONS = (
    "You convert startup research notes into strict JSON. Given research text about candidate "
    "startups/founders (with source URLs), output a JSON object with a single key 'candidates': "
    "an array of objects with exactly these fields — founder_name (string: exactly ONE person's "
    "full name — the primary/first founder mentioned; if the source names multiple co-founders, "
    "put only the first one here, NEVER concatenate multiple names into this field with 'and'/'y'/"
    "commas), co_founders (array of strings: every OTHER named founder/co-founder of the same "
    "startup, each as a separate array entry — empty array if only one founder is named), "
    "startup_name (string), website (string or null), city (string or null), country (string or "
    "null), one_line_description (string), product_stage (one of 'idea', 'mvp', 'launched', "
    "'unknown'), team_size_estimate (integer or null), has_clients (boolean or null), "
    "founded_year (integer or null), funding_status (one of 'bootstrapped', 'pre-seed', "
    "'seed', 'unknown'), tech_stack (array of strings), discovery_signals (array of short "
    "strings explaining why this looks like a promising, low-visibility cold-start candidate), "
    "source_url (the real URL where you found this, required), snippet (a short quote or "
    "paraphrase from the source, required). Only include candidates backed by a real "
    "source_url that actually appeared in the research text — never invent a candidate or URL. "
    "If nothing qualifies, return {\"candidates\": []}."
)

REQUIRED_CANDIDATE_FIELDS = ("founder_name", "startup_name", "one_line_description", "source_url")
