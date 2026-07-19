import PageHeader from "@/components/layout/PageHeader/PageHeader";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import OpportunityGate from "@/components/layout/OpportunityGate/OpportunityGate";
import { startups, getStartup, getTrustScore } from "@/lib/data";
import { fetchLiveStartups, fetchLiveTrustScore } from "@/lib/liveApi";
import TrustSummary from "@/components/sections/trust/components/TrustSummary";
import TrustClaimsList from "@/components/sections/trust/components/TrustClaimsList";

export const dynamic = "force-dynamic";

export default async function TrustPage({
  searchParams,
}: {
  searchParams: Promise<{ startup?: string }>;
}) {
  const params = await searchParams;
  const requestedId = params.startup;

  const liveStartups = await fetchLiveStartups();
  const allStartups = [...liveStartups, ...startups.filter((s) => !liveStartups.some((l) => l.id === s.id))];

  const resolvedId = requestedId && allStartups.some((s) => s.id === requestedId) ? requestedId : null;
  const currentStartup = resolvedId ? allStartups.find((s) => s.id === resolvedId) : undefined;
  const trustScore = resolvedId ? getTrustScore(resolvedId) ?? (await fetchLiveTrustScore(resolvedId)) : undefined;

  return (
    <>
      <PageHeader
        title="Fact Check"
        description="For every claim a startup makes, we show where it came from and how sure we are it's true — and flag anything that doesn't add up."
      />
      {!resolvedId ? (
        <OpportunityGate
          startups={allStartups}
          basePath="/trust"
          title="Whose claims do you want to fact-check?"
          description="Pick a startup to see what they told us, where it came from, and anything that looks off."
        />
      ) : !currentStartup ? (
        <EmptyState icon="confused" title="We couldn't find that startup" />
      ) : (
        <>
          <TrustSummary startups={allStartups} currentStartup={currentStartup} />
          {trustScore ? (
            <TrustClaimsList claims={trustScore.claims} />
          ) : (
            <EmptyState
              icon="archive"
              title="Nothing to check yet"
              description="We haven't recorded any claims for this startup yet."
            />
          )}
        </>
      )}
    </>
  );
}
