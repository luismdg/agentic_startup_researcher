import type { Startup } from "@/lib/types";
import styles from "./PulseStrip.module.css";

export default function PulseStrip({ startups }: { startups: Startup[] }) {
  const total = startups.length;
  const inDecision = startups.filter((s) => s.status === "decision").length;
  const inDiligence = startups.filter((s) => s.status === "diligence").length;
  const avgFit = Math.round(startups.reduce((a, s) => a + s.thesisFitScore, 0) / (total || 1));
  const trendingUp = startups.filter((s) => s.momentumTrend === "up").length;

  const items = [
    { label: "Active opportunities", value: total },
    { label: "In diligence", value: inDiligence },
    { label: "At decision", value: inDecision },
    { label: "Avg. thesis fit", value: `${avgFit}` },
    { label: "Trending up", value: `${trendingUp}/${total}` },
  ];

  return (
    <div className={styles.strip}>
      {items.map((item) => (
        <div key={item.label} className={styles.item}>
          <span className={styles.value}>{item.value}</span>
          <span className={styles.label}>{item.label}</span>
        </div>
      ))}
    </div>
  );
}
