import styles from "./ScoreBar.module.css";

interface ScoreBarProps {
  score: number;
  max?: number;
  color?: string;
  showValue?: boolean;
}

export default function ScoreBar({ score, max = 100, color, showValue = true }: ScoreBarProps) {
  const pct = Math.max(0, Math.min(100, (score / max) * 100));
  return (
    <span className={styles.wrapper}>
      <span className={styles.track}>
        <span
          className={styles.fill}
          style={{
            width: `${pct}%`,
            background: color ?? "var(--color-accent)",
            // box-shadow below uses currentColor, so `color` must track
            // the same dynamic value as `background` for the glow to
            // match the bar instead of inheriting an unrelated ancestor.
            color: color ?? "var(--color-accent)",
          }}
        />
      </span>
      {showValue && <span className={styles.value}>{score}</span>}
    </span>
  );
}
