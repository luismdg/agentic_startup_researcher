import PageHeader from "@/components/layout/PageHeader/PageHeader";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import StartupSwitcher from "@/components/layout/StartupSwitcher/StartupSwitcher";
import OpportunityGate from "@/components/layout/OpportunityGate/OpportunityGate";
import EvaluateHeader from "@/components/sections/evaluate/components/EvaluateHeader";
import EvaluateTabs, { type EvaluateTab } from "@/components/sections/evaluate/components/EvaluateTabs";
import ScreeningView from "@/components/sections/screening/components/ScreeningView";
import DiligenceLogView from "@/components/sections/diligence/components/DiligenceLogView";
import MemoDocument from "@/components/sections/memo/components/MemoDocument";
import DecisionView from "@/components/sections/decision/components/DecisionView";
import { startups, getStartup, getScreening, getDiligenceLog, getMemo } from "@/lib/data";
import { fetchLiveScreening, fetchLiveStartups, fetchLiveMemo } from "@/lib/liveApi";

export const dynamic = "force-dynamic";

const VALID_TABS: EvaluateTab[] = ["scorecard", "checklist", "report", "decision"];

interface EvaluatePageProps {
  searchParams: Promise<{ startup?: string; tab?: string }>;
}

export default async function EvaluatePage({ searchParams }: EvaluatePageProps) {
  const params = await searchParams;
  const requestedId = params.startup;
  const activeTab: EvaluateTab = VALID_TABS.includes(params.tab as EvaluateTab)
    ? (params.tab as EvaluateTab)
    : "scorecard";

  const liveStartups = await fetchLiveStartups();
  const allStartups = [...liveStartups, ...startups.filter((s) => !liveStartups.some((l) => l.id === s.id))];

  const currentId = requestedId && allStartups.some((s) => s.id === requestedId) ? requestedId : null;
  const startup = currentId ? allStartups.find((s) => s.id === currentId) ?? getStartup(currentId) : undefined;

  if (!currentId || !startup) {
    return (
      <>
        <PageHeader
          title="Evaluate"
          description="Everything about one startup, in one place — how it scores, what we've checked, the full write-up, and our call. Switch tabs, not pages."
        />
        <OpportunityGate
          startups={allStartups}
          basePath="/evaluate"
          title="Which startup do you want to evaluate?"
          description="Pick a startup to see its scorecard, checklist, report, and decision — all in one place."
        />
      </>
    );
  }

  const screening = getScreening(currentId) ?? (await fetchLiveScreening(currentId));
  const log = getDiligenceLog(currentId)?.entries ?? [];
  const memo = getMemo(currentId) ?? (await fetchLiveMemo(currentId));

  return (
    <>
      <PageHeader
        title="Evaluate"
        description="Everything about one startup, in one place — how it scores, what we've checked, the full write-up, and our call. Switch tabs, not pages."
      />
      <StartupSwitcher startups={allStartups} currentId={currentId} basePath="/evaluate" />
      <EvaluateHeader startup={startup} />
      <EvaluateTabs
        startupId={currentId}
        activeTab={activeTab}
        panels={{
          scorecard: <ScreeningView startup={startup} screening={screening} />,
          checklist: <DiligenceLogView entries={log} />,
          report: memo ? (
            <MemoDocument memo={memo} />
          ) : (
            <EmptyState
              icon="note"
              title="No report yet"
              description="We haven't put together a report for this startup yet."
            />
          ),
          decision: memo ? (
            <DecisionView startup={startup} decision={memo.decision} />
          ) : (
            <EmptyState
              icon="thinking"
              title="No decision yet"
              description="We haven't written a report for this startup yet, so there's no decision to show."
            />
          ),
        }}
      />
    </>
  );
}
