import type { SourcingFeedItem } from "@/lib/types";
import { formatDate } from "@/lib/data";
import { Table, THead, TBody, TRow, TH, TD } from "@/components/ui/Table/Table";
import TrackBadge from "./TrackBadge";
import SourcingStatusBadge from "./SourcingStatusBadge";
import styles from "./SourcingFeedList.module.css";

export default function SourcingFeedList({ items }: { items: SourcingFeedItem[] }) {
  const sorted = [...items].sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));

  if (sorted.length === 0) {
    return <p className={styles.empty}>No sourcing signals match the current filters.</p>;
  }

  return (
    <Table>
      <THead>
        <tr>
          <TH>Track</TH>
          <TH>Date</TH>
          <TH>Startup</TH>
          <TH>Channel</TH>
          <TH>Summary</TH>
          <TH>Status</TH>
        </tr>
      </THead>
      <TBody>
        {sorted.map((item) => (
          <TRow key={item.id}>
            <TD>
              <TrackBadge track={item.track} />
            </TD>
            <TD>{formatDate(item.date)}</TD>
            <TD>
              <div className={styles.name}>{item.startupName}</div>
              <div className={styles.founders}>{item.founderNames.join(", ")}</div>
              {item.linkedStartupId && (
                <div className={styles.linked}>linked: {item.linkedStartupId}</div>
              )}
            </TD>
            <TD>{item.channel}</TD>
            <TD>
              <div className={styles.summary}>{item.summary}</div>
              {item.track === "outbound" && item.activated && item.activatedDate && (
                <div className={styles.activatedNote}>
                  Activated into application &middot; {formatDate(item.activatedDate)}
                </div>
              )}
            </TD>
            <TD>
              <SourcingStatusBadge status={item.status} />
            </TD>
          </TRow>
        ))}
      </TBody>
    </Table>
  );
}
