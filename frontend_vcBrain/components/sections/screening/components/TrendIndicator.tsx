import type { Trend } from "@/lib/types";
import TrendArrow from "@/components/ui/TrendArrow/TrendArrow";
import styles from "./TrendIndicator.module.css";

interface TrendIndicatorProps {
  trend: Trend;
}

/**
 * Thin wrapper around the shared TrendArrow ui component, scoped to the
 * screening section so each axis column can render its own independent
 * trend glyph without pulling in extra layout assumptions.
 */
export default function TrendIndicator({ trend }: TrendIndicatorProps) {
  return (
    <span className={styles.indicator}>
      <TrendArrow trend={trend} />
    </span>
  );
}
