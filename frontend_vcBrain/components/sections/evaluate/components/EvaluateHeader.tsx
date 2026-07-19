import type { Startup } from "@/lib/types";
import Badge from "@/components/ui/Badge/Badge";
import StatusBadge from "@/components/ui/StatusBadge/StatusBadge";
import TrendArrow from "@/components/ui/TrendArrow/TrendArrow";
import styles from "./EvaluateHeader.module.css";

/**
 * One shared identity strip for the whole Evaluate section, shown once above
 * the tabs -- Scorecard/Checklist/Report/Decision each used to render their
 * own near-identical name/sector/stage row; consolidating it here is the
 * actual point of merging these into one section, not just moving files.
 */
export default function EvaluateHeader({ startup }: { startup: Startup }) {
  return (
    <div className={styles.header}>
      <div className={styles.identity}>
        <h2 className={styles.name}>{startup.name}</h2>
        <p className={styles.tagline}>{startup.tagline}</p>
        <div className={styles.badges}>
          <Badge variant="neutral">{startup.sector}</Badge>
          <Badge variant="neutral">{startup.stage}</Badge>
          <Badge variant="neutral">{startup.geography}</Badge>
          <StatusBadge status={startup.status} />
        </div>
      </div>
      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Thesis fit</span>
          <span className={styles.statValue}>{startup.thesisFitScore}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Momentum</span>
          <TrendArrow trend={startup.momentumTrend} />
        </div>
      </div>
    </div>
  );
}
