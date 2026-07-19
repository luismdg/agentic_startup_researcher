import PageHeader from "@/components/layout/PageHeader/PageHeader";
import StartupSwitcher from "@/components/layout/StartupSwitcher/StartupSwitcher";
import OpportunityGate from "@/components/layout/OpportunityGate/OpportunityGate";
import DiligenceLogView from "@/components/sections/diligence/components/DiligenceLogView";
import { startups, getStartup, getDiligenceLog } from "@/lib/data";
import styles from "./page.module.css";

export default async function DiligencePage({
  searchParams,
}: {
  searchParams: Promise<{ startup?: string }>;
}) {
  const params = await searchParams;
  const requestedId = params.startup;
  const isValidId = Boolean(requestedId) && startups.some((s) => s.id === requestedId);
  const currentId = isValidId ? (requestedId as string) : null;

  const startup = currentId ? getStartup(currentId) ?? startups[0] : null;
  const log = currentId ? getDiligenceLog(currentId) : undefined;
  const entries = log?.entries ?? [];

  return (
    <>
      <PageHeader
        title="Checklist"
        description="Everything we've checked so far — and everything still left to check — for each startup."
      />
      {!currentId || !startup ? (
        <OpportunityGate
          startups={startups}
          basePath="/diligence"
          title="Whose checklist do you want to open?"
          description="Pick a startup to see what's confirmed, what's still open, and anything that didn't check out."
        />
      ) : (
        <>
          <StartupSwitcher startups={startups} currentId={startup.id} basePath="/diligence" />
          <p className={styles.summary}>
            <strong className={styles.name}>{startup.name}</strong>
            <span className={styles.sep} aria-hidden="true">
              ·
            </span>
            {startup.sector}
            <span className={styles.sep} aria-hidden="true">
              ·
            </span>
            {startup.stage}
            <span className={styles.sep} aria-hidden="true">
              ·
            </span>
            {startup.geography}
            <span className={styles.sep} aria-hidden="true">
              ·
            </span>
            {entries.length} logged {entries.length === 1 ? "entry" : "entries"}
          </p>
          <DiligenceLogView entries={entries} />
        </>
      )}
    </>
  );
}
