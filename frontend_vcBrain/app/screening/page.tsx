import PageHeader from "@/components/layout/PageHeader/PageHeader";
import StartupSwitcher from "@/components/layout/StartupSwitcher/StartupSwitcher";
import OpportunityGate from "@/components/layout/OpportunityGate/OpportunityGate";
import ScreeningView from "@/components/sections/screening/components/ScreeningView";
import { startups, getStartup, getScreening } from "@/lib/data";
import { fetchLiveScreening, fetchLiveStartups } from "@/lib/liveApi";

export const dynamic = "force-dynamic";

interface ScreeningPageProps {
  searchParams: Promise<{ startup?: string }>;
}

export default async function ScreeningPage({ searchParams }: ScreeningPageProps) {
  const params = await searchParams;
  const requestedId = params.startup;

  const liveStartups = await fetchLiveStartups();
  const allStartups = [...liveStartups, ...startups.filter((s) => !liveStartups.some((l) => l.id === s.id))];

  const currentId = requestedId && allStartups.some((s) => s.id === requestedId) ? requestedId : null;
  const currentStartup = currentId ? allStartups.find((s) => s.id === currentId) : undefined;
  const screening = currentId ? getScreening(currentId) ?? (await fetchLiveScreening(currentId)) : undefined;

  return (
    <>
      <PageHeader
        title="Scorecard"
        description="We score three separate things — the founders, the market, and the idea — and never blend them into one number. A great founder in a so-so market shouldn't get lost in an average."
      />
      {!currentId || !currentStartup ? (
        <OpportunityGate
          startups={allStartups}
          basePath="/screening"
          title="Whose scorecard do you want to see?"
          description="Pick a startup to see how its founders, market, and idea each score on their own — nothing shows until you choose."
        />
      ) : (
        <>
          <StartupSwitcher startups={allStartups} currentId={currentId} basePath="/screening" />
          <ScreeningView startup={currentStartup} screening={screening} />
        </>
      )}
    </>
  );
}
