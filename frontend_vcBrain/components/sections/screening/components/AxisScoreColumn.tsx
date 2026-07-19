import type { AxisScore } from "@/lib/types";
import ScoreBar from "@/components/ui/ScoreBar/ScoreBar";
import TrendIndicator from "./TrendIndicator";
import styles from "./AxisScoreColumn.module.css";

interface AxisScoreColumnProps {
  label: string;
  colorVar: string;
  data: AxisScore;
}

/**
 * One independent axis track (Founder / Market / Idea-vs-Market). Deliberately
 * never combined with the other axes — each column owns its own score,
 * trend, color identity, and rationale text.
 */
export default function AxisScoreColumn({ label, colorVar, data }: AxisScoreColumnProps) {
  return (
    <div className={styles.column}>
      <div className={styles.header}>
        <span className={styles.label}>{label}</span>
        <TrendIndicator trend={data.trend} />
      </div>
      <div className={styles.score} style={{ color: colorVar }}>
        {data.score}
      </div>
      <div className={styles.bar}>
        <ScoreBar score={data.score} color={colorVar} showValue={false} />
      </div>
      <p className={styles.rationale}>{data.rationale}</p>
    </div>
  );
}
