from datetime import datetime, timezone


def trace_line(message: str) -> str:
    """A single agent_trace entry, timestamped so the ordered log (Section 8's
    `agent_trace`) is reconstructible after the fact."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    return f"[{ts}] {message}"
