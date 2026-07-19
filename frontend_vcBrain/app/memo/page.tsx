import PageHeader from "@/components/layout/PageHeader/PageHeader";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import StartupSwitcher from "@/components/layout/StartupSwitcher/StartupSwitcher";
import OpportunityGate from "@/components/layout/OpportunityGate/OpportunityGate";
import MemoDocument from "@/components/sections/memo/components/MemoDocument";
import { startups, getStartup, getMemo } from "@/lib/data";
import { fetchLiveMemo, fetchLiveStartups } from "@/lib/liveApi";

export const dynamic = "force-dynamic";

export default async function MemoPage({
  searchParams,
}: {
  searchParams: Promise<{ startup?: string }>;
}) {
  const params = await searchParams;
  const requestedId = params.startup;

  const liveStartups = await fetchLiveStartups();
  const allStartups = [...liveStartups, ...startups.filter((s) => !liveStartups.some((l) => l.id === s.id))];

  const currentId = requestedId && allStartups.some((s) => s.id === requestedId) ? requestedId : null;
  const startup = currentId ? allStartups.find((s) => s.id === currentId) : undefined;
  const memo = currentId ? getMemo(currentId) ?? (await fetchLiveMemo(currentId)) : undefined;

  return (
    <>
      <PageHeader
        title="Report"
        description={
          startup
            ? `${startup.name} — the full write-up, put together for you.`
            : "The full write-up on a startup — company basics, strengths and risks, traction, and more."
        }
      />
      {!currentId ? (
        <OpportunityGate
          startups={allStartups}
          basePath="/memo"
          title="Whose report do you want to read?"
          description="Pick a startup and we'll put together the full write-up: what it does, why it might work, and what could go wrong."
        />
      ) : (
        <>
          <StartupSwitcher startups={allStartups} currentId={currentId} basePath="/memo" />
          {memo ? (
            <MemoDocument memo={memo} />
          ) : (
            <EmptyState
              icon="note"
              title="No report yet"
              description="We haven't put together a report for this startup yet."
            />
          )}
        </>
      )}
    </>
  );
}
