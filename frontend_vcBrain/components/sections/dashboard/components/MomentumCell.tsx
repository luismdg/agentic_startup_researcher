import type { MomentumPoint, Trend } from "@/lib/types";
import SparkLine from "@/components/ui/SparkLine/SparkLine";
import TrendArrow from "@/components/ui/TrendArrow/TrendArrow";
import styles from "./MomentumCell.module.css";

const TREND_COLOR: Record<Trend, string> = {
  up: "var(--color-trend-up)",
  down: "var(--color-trend-down)",
  flat: "var(--color-trend-flat)",
};

export default function MomentumCell({
  history,
  trend,
}: {
  history: MomentumPoint[];
  trend: Trend;
}) {
  return (
    <div className={styles.cell}>
      <SparkLine values={history.map((h) => h.score)} colorVar={TREND_COLOR[trend]} />
      <TrendArrow trend={trend} label={false} />
    </div>
  );
}
