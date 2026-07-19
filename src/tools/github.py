import httpx

from src.config import mock_mode
from src.models.candidate import EvidenceItem
from src.models.pipeline import RawCandidate
from src.tools.base import mock_candidates_for, today_iso
from src.utils.tracing import trace_line

SOURCE = "github"


async def search(
    query: str, niche: str, discovery_pass: int, filters_context: str = ""
) -> tuple[list[RawCandidate], list[str]]:
    trace: list[str] = []
    if mock_mode(SOURCE):
        return mock_candidates_for(SOURCE, niche, query, discovery_pass), trace

    try:
        candidates = await _real_search(query, niche, discovery_pass, trace)
        return candidates, trace
    except Exception as exc:
        trace.append(trace_line(f"[github] real API call failed ({exc})"))
        return mock_candidates_for(SOURCE, niche, query, discovery_pass), trace


async def _real_search(
    query: str, niche: str, discovery_pass: int, trace: list[str]
) -> list[RawCandidate]:
    headers = {"Accept": "application/vnd.github+json"}

    params = {"q": f"{query} in:name,description", "sort": "updated", "per_page": 5}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.github.com/search/repositories", headers=headers, params=params
        )
        resp.raise_for_status()
        repos = resp.json().get("items", [])

    trace.append(trace_line(f"[github] real search for '{query}' returned {len(repos)} repos"))

    candidates = []
    for repo in repos:
        owner = repo.get("owner", {}) or {}
        candidates.append(
            RawCandidate(
                founder_name=owner.get("login", "Unknown"),
                founder_city=None,
                founder_country=None,
                founder_linkedin=None,
                startup_name=repo.get("name", "Unknown project"),
                website=repo.get("homepage") or repo.get("html_url"),
                niche=niche,
                one_line_description=(repo.get("description") or "No description available.")[:280],
                product_stage="unknown",
                tech_stack_signals=[repo["language"]] if repo.get("language") else [],
                traction_signals={
                    "github_repo_url": repo.get("html_url"),
                    "github_commit_activity": f"last pushed {repo.get('pushed_at', 'unknown')}",
                },
                source_channel="GitHub",
                search_queries_used=[query],
                discovery_signals=[
                    f"GitHub repo matched search, {repo.get('stargazers_count', 0)} stars, "
                    f"owner is a repo account, not verified as a named founder"
                ],
                discovery_pass=discovery_pass,
                evidence=[
                    EvidenceItem(
                        source_url=repo.get("html_url", ""),
                        snippet=(repo.get("description") or "")[:200],
                        date_captured=today_iso(),
                    )
                ],
                date_found=today_iso(),
            )
        )
    return candidates
