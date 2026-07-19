import type { Confidence } from "@/lib/types";
import styles from "./ConfidenceMeter.module.css";

const LEVELS: Confidence[] = ["low", "medium", "high"];
const FILL_COUNT: Record<Confidence, number> = { low: 1, medium: 2, high: 3 };
const LABEL: Record<Confidence, string> = { low: "Low confidence", medium: "Medium confidence", high: "High confidence" };

export default function ConfidenceMeter({ level }: { level: Confidence }) {
  const filled = FILL_COUNT[level];
  return (
    <span className={styles.meter} title={LABEL[level]}>
      <span className={styles.dots}>
        {LEVELS.map((_, i) => (
          <span
            key={i}
            className={`${styles.dot} ${i < filled ? styles[`dot-${level}`] : ""}`}
          />
        ))}
      </span>
      <span className={`${styles.text} ${styles[level]}`}>{LABEL[level]}</span>
    </span>
  );
}
