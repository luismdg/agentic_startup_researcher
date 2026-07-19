import type { Startup } from "@/lib/types";
import StartupSwitcher from "@/components/layout/StartupSwitcher/StartupSwitcher";
import styles from "./TrustSummary.module.css";

interface TrustSummaryProps {
  startups: Startup[];
  currentStartup: Startup;
}

export default function TrustSummary({ startups, currentStartup }: TrustSummaryProps) {
  return (
    <div>
      <StartupSwitcher startups={startups} currentId={currentStartup.id} basePath="/trust" />
      <div className={styles.line}>
        <span className={styles.name}>{currentStartup.name}</span>
        <span className={styles.separator}>—</span>
        <span className={styles.hint}>
          Every claim below is checked on its own — there&rsquo;s no single trust score for the
          company as a whole.
        </span>
      </div>
    </div>
  );
}
