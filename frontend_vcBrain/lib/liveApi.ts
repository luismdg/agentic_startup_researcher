import type { Memo, Screening, SourcingFeedItem, Startup, TrustScoreRecord } from "./types";

// reasoning-engine's FastAPI server (see reasoning-engine/app/api_routes.py).
// Overridable via env so a deployed build can point elsewhere; defaults to
// the local dev port used throughout this project.
const LIVE_API_BASE = process.env.REASONING_API_URL ?? "http://127.0.0.1:8001";

/**
 * Every function here fails safe: if reasoning-engine isn't running, or a
 * startup was never ingested there, these return an empty/undefined result
 * instead of throwing -- the rest of the app already handles "no live data"
 * identically to "no mock data" (EmptyState, OpportunityGate, etc.), so a
 * live-fetch failure degrades to exactly the same UI as before this existed,
 * never a broken page.
 */
async function liveFetch<T>(path: string): Promise<T | undefined> {
  try {
    const res = await fetch(`${LIVE_API_BASE}${path}`, { cache: "no-store" });
    if (!res.ok) return undefined;
    return (await res.json()) as T;
  } catch {
    return undefined;
  }
}

export async function fetchLiveStartups(): Promise<Startup[]> {
  return (await liveFetch<Startup[]>("/api/startups")) ?? [];
}

export async function fetchLiveScreening(startupId: string): Promise<Screening | undefined> {
  return liveFetch<Screening>(`/api/startups/${startupId}/screening`);
}

export async function fetchLiveTrustScore(startupId: string): Promise<TrustScoreRecord | undefined> {
  return liveFetch<TrustScoreRecord>(`/api/startups/${startupId}/trust`);
}

export async function fetchLiveMemo(startupId: string): Promise<Memo | undefined> {
  return liveFetch<Memo>(`/api/startups/${startupId}/memo`);
}

export async function fetchLiveSourcingFeed(): Promise<SourcingFeedItem[]> {
  return (await liveFetch<SourcingFeedItem[]>("/api/sourcing/feed")) ?? [];
}
