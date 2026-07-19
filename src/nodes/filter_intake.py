"""Node 1 — Filter Intake. Receives the one-time filter submission from the
frontend's guided search panel and normalizes it. Does not hard-reject
unrecognized values (Node 2 has its own fallback-resolution logic for
niches); it only records what it saw for traceability."""

from src.models.filters import SearchFilters
from src.services.data_store import load_filter_options
from src.utils.tracing import trace_line


def intake(filters: SearchFilters) -> tuple[SearchFilters, list[str]]:
    options = load_filter_options()
    trace = [trace_line(f"Node 1 (filter_intake): received niche='{filters.niche}'")]

    if filters.niche not in options["niches"]:
        trace.append(
            trace_line(
                f"Node 1: niche '{filters.niche}' not in filter-options.json — "
                "Node 2 will resolve it via fallback"
            )
        )
    if filters.geography and filters.geography not in options["geographies"]:
        trace.append(trace_line(f"Node 1: geography '{filters.geography}' not in known list, kept as-is"))
    unknown_channels = [c for c in filters.channels if c not in options["channels"]]
    if unknown_channels:
        trace.append(trace_line(f"Node 1: unrecognized channels {unknown_channels}, kept as-is"))
    if filters.stage_signal and filters.stage_signal not in options["stage_signals"]:
        trace.append(trace_line(f"Node 1: stage_signal '{filters.stage_signal}' not in known list, kept as-is"))

    return filters, trace
