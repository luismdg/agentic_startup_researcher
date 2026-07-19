import type { FounderTimelineEvent } from "@/lib/types";
import { formatDate } from "@/lib/data";
import styles from "./FounderTimeline.module.css";

export default function FounderTimeline({ events }: { events: FounderTimelineEvent[] }) {
  if (events.length === 0) {
    return <p className={styles.empty}>No timeline events recorded.</p>;
  }

  return (
    <ol className={styles.timeline}>
      {events.map((event, i) => (
        <li key={`${event.date}-${i}`} className={styles.entry}>
          <span className={styles.marker} aria-hidden="true">
            <span className={styles.dot} />
          </span>
          <div className={styles.content}>
            <div className={styles.date}>{formatDate(event.date)}</div>
            <div className={styles.label}>{event.label}</div>
            <div className={styles.detail}>{event.detail}</div>
          </div>
        </li>
      ))}
    </ol>
  );
}
