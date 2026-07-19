import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache
def load_filter_options() -> dict:
    return json.loads((DATA_DIR / "filter-options.json").read_text(encoding="utf-8"))


@lru_cache
def load_niche_profiles() -> dict:
    return json.loads((DATA_DIR / "niche-search-profiles.json").read_text(encoding="utf-8"))


@lru_cache
def load_mock_search_results() -> dict:
    return json.loads((DATA_DIR / "mock-search-results.json").read_text(encoding="utf-8"))


@lru_cache
def load_channel_vocabulary() -> dict:
    """Per-source terminology (typical_labels/typical_events/framing) — how
    people actually talk about their startup differs by channel (LinkedIn:
    'MVP'/'Co-founder'/'Summit'; GitHub: 'hackathon'/'agentic'/'WIP'; Reddit:
    'feedback wanted'; etc). Used by Node 3 (query wording) and the OpenAI
    web-research agent (browsing framing) so both actually search in the
    vocabulary each channel uses, not one generic phrasing everywhere."""
    return json.loads((DATA_DIR / "channel-vocabulary.json").read_text(encoding="utf-8"))


def load_known_startups() -> list[dict]:
    # Not lru_cache'd: this file is appended to at the end of a run (see
    # append_known_startups), so callers need the current on-disk state.
    return json.loads((DATA_DIR / "known-startups.json").read_text(encoding="utf-8"))[
        "known_startups"
    ]


def append_known_startups(new_entries: list[dict]) -> None:
    """Grows the system's dedup memory (Section 6a) with genuinely_new,
    medium/high-confidence candidates from a completed run, so future runs
    dedup against them too."""
    if not new_entries:
        return
    path = DATA_DIR / "known-startups.json"
    current = json.loads(path.read_text(encoding="utf-8"))
    existing_names = {s["startup_name"] for s in current["known_startups"]}
    for entry in new_entries:
        if entry["startup_name"] not in existing_names:
            current["known_startups"].append(entry)
            existing_names.add(entry["startup_name"])
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
