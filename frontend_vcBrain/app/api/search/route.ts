import { NextResponse } from "next/server";

// Same defaults as lib/liveApi.ts -- this route is the server-side-only
// counterpart: it talks to the sourcing backend (port 8000) too, which the
// browser never should directly (different response schema, and CORS on
// that service is scoped to the frontend's own origin regardless).
const SOURCING_API_BASE = process.env.SOURCING_API_URL ?? "http://127.0.0.1:8000";
const REASONING_API_BASE = process.env.REASONING_API_URL ?? "http://127.0.0.1:8001";

interface SearchRequestBody {
  niche: string;
  geography?: string;
  keywords?: string[];
  channels?: string[];
  stageSignal?: string;
  maxResults?: number;
}

export async function POST(request: Request) {
  let body: SearchRequestBody;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Request body was not valid JSON." }, { status: 400 });
  }

  if (!body.niche || !body.niche.trim()) {
    return NextResponse.json({ ok: false, error: "Niche is required." }, { status: 400 });
  }

  const searchFilters = {
    niche: body.niche.trim(),
    founder_view: false, // Discover is always startup-centric -- SourcingFeedItem already lists co-founders per row
    geography: body.geography?.trim() || undefined,
    channels: body.channels ?? [],
    stage_signal: body.stageSignal || undefined,
    keywords: body.keywords ?? [],
    max_results: body.maxResults ?? 10,
  };

  let searchResponse: Response;
  try {
    searchResponse = await fetch(`${SOURCING_API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(searchFilters),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      {
        ok: false,
        error: `Couldn't reach the sourcing backend at ${SOURCING_API_BASE}. Is it running? See root README.md "Running the full stack".`,
      },
      { status: 502 }
    );
  }

  if (!searchResponse.ok) {
    const detail = await searchResponse.text().catch(() => "");
    return NextResponse.json(
      { ok: false, error: `Sourcing backend returned ${searchResponse.status}. ${detail}`.trim() },
      { status: 502 }
    );
  }

  const searchResult = await searchResponse.json();
  const resultsFound: number = searchResult.results?.length ?? 0;

  if (resultsFound === 0) {
    return NextResponse.json({ ok: true, resultsFound: 0, ingested: 0 });
  }

  // The one real schema mismatch between the two backends -- see root
  // README.md §6: the sourcing backend wraps run metadata as "run",
  // reasoning-engine's ingest endpoint expects the identical object as "query".
  const ingestPayload = { query: searchResult.run, results: searchResult.results };

  let ingestResponse: Response;
  try {
    ingestResponse = await fetch(`${REASONING_API_BASE}/api/sourcing/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ingestPayload),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      {
        ok: false,
        error: `Search found ${resultsFound} candidate(s), but couldn't reach reasoning-engine at ${REASONING_API_BASE} to score/ingest them. Is it running?`,
        resultsFound,
      },
      { status: 502 }
    );
  }

  if (!ingestResponse.ok) {
    const detail = await ingestResponse.text().catch(() => "");
    // reasoning-engine's scoring/memo calls are NOT fail-safe the way sourcing's
    // are (see README troubleshooting note) -- a network/key issue there
    // surfaces as a real error here, not a silent empty result.
    return NextResponse.json(
      {
        ok: false,
        error: `Search found ${resultsFound} candidate(s), but reasoning-engine failed to score/ingest them (${ingestResponse.status}). This usually means its OPENAI_API_KEY/network isn't working -- check its terminal output. ${detail}`.trim(),
        resultsFound,
      },
      { status: 502 }
    );
  }

  const ingestResult = await ingestResponse.json();
  return NextResponse.json({ ok: true, resultsFound, ingested: ingestResult.ingested ?? 0 });
}
