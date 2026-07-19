import PageHeader from "@/components/layout/PageHeader/PageHeader";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import StartupSwitcher from "@/components/layout/StartupSwitcher/StartupSwitcher";
import OpportunityGate from "@/components/layout/OpportunityGate/OpportunityGate";
import DecisionView from "@/components/sections/decision/components/DecisionView";
import { startups, getStartup, getMemo } from "@/lib/data";

interface DecisionPageProps {
  searchParams: Promise<{ startup?: string }>;
}

export default async function DecisionPage({ searchParams }: DecisionPageProps) {
  const params = await searchParams;
  const requestedId = params.startup;
  const currentId = requestedId && startups.some((s) => s.id === requestedId) ? requestedId : null;

  const startup = currentId ? getStartup(currentId) : undefined;
  const memo = currentId ? getMemo(currentId) : undefined;

  return (
    <>
      <PageHeader
        title="Decision"
        description="Should we write the $100K check? Here's our answer, the strongest case against it, and how it fits with what else we own — kept separate on purpose, not blended into one opinion."
      />
      {!currentId || !startup ? (
        <OpportunityGate
          startups={startups}
          basePath="/decision"
          title="Which startup do you want a decision on?"
          description="Pick a startup to see our answer, the case against it, and how it fits with the rest of what we've invested in."
        />
      ) : (
        <>
          <StartupSwitcher startups={startups} currentId={currentId} basePath="/decision" />
          {memo ? (
            <DecisionView startup={startup} decision={memo.decision} />
          ) : (
            <EmptyState
              icon="thinking"
              title="No decision yet"
              description="We haven't written a report for this startup yet, so there's no decision to show."
            />
          )}
        </>
      )}
    </>
  );
}
