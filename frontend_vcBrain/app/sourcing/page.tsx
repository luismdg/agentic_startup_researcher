import PageHeader from "@/components/layout/PageHeader/PageHeader";
import SourcingView from "@/components/sections/sourcing/components/SourcingView";
import AgenticSearchForm from "@/components/sections/sourcing/components/AgenticSearchForm";
import { sourcingFeed, sourcingChannels, founders } from "@/lib/data";
import { fetchLiveSourcingFeed } from "@/lib/liveApi";

// Live-ingested leads from reasoning-engine (see lib/liveApi.ts) change
// whenever someone ingests a new sourcing run, so this can't be statically
// prerendered -- same reasoning as app/page.tsx.
export const dynamic = "force-dynamic";

interface SourcingPageProps {
  searchParams: Promise<{ founder?: string }>;
}

export default async function SourcingPage({ searchParams }: SourcingPageProps) {
  const { founder } = await searchParams;
  const liveFeed = await fetchLiveSourcingFeed();
  // Live leads first (freshest), mock feed fills in the rest -- never
  // duplicate a mock entry that happens to share an id, same merge rule
  // app/page.tsx uses for startups.
  const feed = [...liveFeed, ...sourcingFeed.filter((f) => !liveFeed.some((l) => l.id === f.id))];

  return (
    <>
      <PageHeader
        title="Discover"
        description="New startups, in one place — the ones that applied to you, and the ones we found for you on GitHub, Google, and beyond."
      />
      <AgenticSearchForm />
      <SourcingView
        feed={feed}
        channels={sourcingChannels}
        founders={founders}
        liveFeed={liveFeed}
        selectedFounderId={founder}
      />
    </>
  );
}
