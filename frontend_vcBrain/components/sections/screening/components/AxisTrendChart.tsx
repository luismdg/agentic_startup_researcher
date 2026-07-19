import type { ScreeningHistoryPoint } from "@/lib/types";
import { formatDate } from "@/lib/data";
import styles from "./AxisTrendChart.module.css";

type SeriesKey = "founder" | "market" | "idea";

interface Series {
  key: SeriesKey;
  label: string;
  colorVar: string;
}

const SERIES: Series[] = [
  { key: "founder", label: "Founder", colorVar: "var(--color-axis-founder)" },
  { key: "market", label: "Market", colorVar: "var(--color-axis-market)" },
  { key: "idea", label: "Idea × Market Fit", colorVar: "var(--color-axis-idea)" },
];

const WIDTH = 640;
const HEIGHT = 160;
const PADDING = 8;

/**
 * Local, section-specific multi-line chart for the 5-point screening history.
 * Follows the same hand-rolled-SVG technique as components/ui/SparkLine
 * (min/max scaling, polyline per series) but scales all three axes across a
 * single shared y-range so the three lines stay comparable, and renders three
 * polylines instead of one.
 */
export default function AxisTrendChart({ history }: { history: ScreeningHistoryPoint[] }) {
  if (history.length === 0) return null;

  const allValues = history.flatMap((point) => [point.founder, point.market, point.idea]);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min || 1;
  const stepX = (WIDTH - PADDING * 2) / (history.length - 1 || 1);

  const toX = (index: number) => PADDING + index * stepX;
  const toY = (value: number) => HEIGHT - PADDING - ((value - min) / range) * (HEIGHT - PADDING * 2);

  const buildPoints = (key: SeriesKey) =>
    history.map((point, index) => `${toX(index).toFixed(1)},${toY(point[key]).toFixed(1)}`).join(" ");

  return (
    <div className={styles.wrapper}>
      <div className={styles.legend}>
        {SERIES.map((series) => (
          <span key={series.key} className={styles.legendItem}>
            <span className={styles.dot} style={{ background: series.colorVar }} aria-hidden="true" />
            {series.label}
          </span>
        ))}
      </div>
      <svg
        className={styles.chart}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="Founder, market, and idea-market fit scores over the last five months"
      >
        {SERIES.map((series) => (
          <polyline
            key={series.key}
            points={buildPoints(series.key)}
            fill="none"
            stroke={series.colorVar}
            strokeWidth={2}
          />
        ))}
        {SERIES.flatMap((series) =>
          history.map((point, index) => (
            <circle
              key={`${series.key}-${point.date}`}
              cx={toX(index)}
              cy={toY(point[series.key])}
              r={2.5}
              fill={series.colorVar}
            />
          ))
        )}
      </svg>
      <div className={styles.axisLabels}>
        {history.map((point) => (
          <span key={point.date} className={styles.axisLabel}>
            {formatDate(point.date)}
          </span>
        ))}
      </div>
    </div>
  );
}
