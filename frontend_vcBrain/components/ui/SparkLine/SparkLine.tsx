import styles from "./SparkLine.module.css";

interface SparkLineProps {
  values: number[];
  width?: number;
  height?: number;
  colorVar?: string;
}

export default function SparkLine({
  values,
  width = 96,
  height = 28,
  colorVar = "var(--color-accent)",
}: SparkLineProps) {
  if (values.length === 0) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = width / (values.length - 1 || 1);
  const points = values.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / range) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const last = values[values.length - 1];
  const lastY = height - ((last - min) / range) * height;

  return (
    <svg
      className={styles.spark}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Trend from ${values[0]} to ${last}`}
    >
      <polyline points={points.join(" ")} fill="none" stroke={colorVar} strokeWidth={1.5} />
      <circle cx={width} cy={lastY} r={2} fill={colorVar} />
    </svg>
  );
}
