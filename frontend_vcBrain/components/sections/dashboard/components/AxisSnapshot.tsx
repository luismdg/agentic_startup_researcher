import type { Screening } from "@/lib/types";
import styles from "./AxisSnapshot.module.css";

interface AxisSnapshotProps {
  screening?: Screening;
}

/**
 * Three independent numbers — never combined into one score. Mirrors the
 * Scorecard page's axis columns, just compact enough for a list row.
 */
export default function AxisSnapshot({ screening }: AxisSnapshotProps) {
  if (!screening) {
    return <span className={styles.empty}>Not scored yet</span>;
  }

  return (
    <span className={styles.snapshot}>
      <span className={styles.chip} style={{ color: "var(--color-axis-founder)" }} title="People">
        {screening.founder.score}
      </span>
      <span className={styles.sep} aria-hidden="true">
        /
      </span>
      <span className={styles.chip} style={{ color: "var(--color-axis-market)" }} title="Market">
        {screening.market.score}
      </span>
      <span className={styles.sep} aria-hidden="true">
        /
      </span>
      <span className={styles.chip} style={{ color: "var(--color-axis-idea)" }} title="Idea fit">
        {screening.ideaMarketFit.score}
      </span>
    </span>
  );
}
