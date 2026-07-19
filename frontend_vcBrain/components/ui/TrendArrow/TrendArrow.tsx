import type { Trend } from "@/lib/types";
import Icon, { type IconName } from "@/components/ui/Icon/Icon";
import styles from "./TrendArrow.module.css";

const ICON: Record<Trend, IconName> = { up: "trendUp", down: "trendDown", flat: "trendFlat" };
const LABEL: Record<Trend, string> = { up: "Improving", down: "Declining", flat: "Stable" };

export default function TrendArrow({ trend, label = true }: { trend: Trend; label?: boolean }) {
  return (
    <span className={`${styles.trend} ${styles[trend]}`} title={LABEL[trend]}>
      <Icon name={ICON[trend]} size={13} />
      {label && <span className={styles.label}>{LABEL[trend]}</span>}
    </span>
  );
}
