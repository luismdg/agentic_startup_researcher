import PageHeader from "@/components/layout/PageHeader/PageHeader";
import DashboardView from "@/components/sections/dashboard/components/DashboardView";
import HeroConstellation from "@/components/sections/dashboard/components/HeroConstellation";
import { startups, getScreening } from "@/lib/data";
import { fetchLiveScreening, fetchLiveStartups } from "@/lib/liveApi";
import type { Screening, Startup } from "@/lib/types";

// This page ingests live data from reasoning-engine on every request (see
// lib/liveApi.ts) -- it can never be statically prerendered, since a record
// ingested after build time still needs to show up here.
export const dynamic = "force-dynamic";

async function pickFeatured(allStartups: Startup[]): Promise<{ startup: Startup; screening: Screening } | undefined> {
  const ranked = [...allStartups].sort((a, b) => b.thesisFitScore - a.thesisFitScore);
  for (const startup of ranked) {
    const screening = getScreening(startup.id) ?? (await fetchLiveScreening(startup.id));
    if (screening) return { startup, screening };
  }
  return undefined;
}

export default async function DashboardPage() {
  const liveStartups = await fetchLiveStartups();
  // Live-sourced startups take priority in ordering (freshest, most likely
  // relevant to whatever was just ingested) but never duplicate a static
  // mock entry that happens to share an id.
  const allStartups = [...liveStartups, ...startups.filter((s) => !liveStartups.some((l) => l.id === s.id))];
  const featured = await pickFeatured(allStartups);

  const liveScreeningEntries = await Promise.all(
    liveStartups.map(async (s) => [s.id, await fetchLiveScreening(s.id)] as const)
  );
  const liveScreenings = Object.fromEntries(
    liveScreeningEntries.filter((entry): entry is [string, Screening] => Boolean(entry[1]))
  );

  return (
    <>
      <HeroConstellation startups={allStartups} featured={featured} />
      <PageHeader
        title="Overview"
        description="A quick look at every startup you're watching, best first. Tell us what you care about and we'll rank them for you."
      />
      <DashboardView startups={allStartups} liveScreenings={liveScreenings} />
    </>
  );
}
