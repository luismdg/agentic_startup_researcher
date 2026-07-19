import Link from "next/link";
import type { SourcingFeedItem } from "@/lib/types";
import { formatDate } from "@/lib/data";
import { Table, THead, TBody, TRow, TH, TD } from "@/components/ui/Table/Table";
import Badge from "@/components/ui/Badge/Badge";
import styles from "./LiveFoundersList.module.css";

interface FounderRow {
  id: string;
  name: string;
  startupName: string;
  linkedStartupId: string | null;
  channel: string;
  date: string;
}

/**
 * Founders as the agentic pipeline actually reported them -- name, which
 * startup, which channel, when. Deliberately not the richer mock Founder
 * shape (founderScore, archetype, timeline, priorVentures with years):
 * nothing upstream provides those for a live-sourced person, and inventing
 * them would be exactly the kind of fabricated data this codebase's
 * EmptyValue/MemoField pattern exists to avoid everywhere else.
 */
export default function LiveFoundersList({ feed }: { feed: SourcingFeedItem[] }) {
  const rows: FounderRow[] = feed.flatMap((item) =>
    item.founderNames.map((name, i) => ({
      id: `${item.id}_${i}`,
      name,
      startupName: item.startupName,
      linkedStartupId: item.linkedStartupId,
      channel: item.channel,
      date: item.date,
    }))
  );

  if (rows.length === 0) {
    return (
      <p className={styles.empty}>
        No founders from a live search yet — run one above and they&rsquo;ll show up here.
      </p>
    );
  }

  return (
    <Table>
      <THead>
        <tr>
          <TH>Founder</TH>
          <TH>Startup</TH>
          <TH>Found via</TH>
          <TH align="right">Date</TH>
        </tr>
      </THead>
      <TBody>
        {rows.map((row) => (
          <TRow key={row.id}>
            <TD>
              <span className={styles.name}>{row.name}</span>
            </TD>
            <TD>
              {row.linkedStartupId ? (
                <Link href={`/evaluate?startup=${row.linkedStartupId}`} className={styles.startupLink}>
                  {row.startupName}
                </Link>
              ) : (
                row.startupName
              )}
            </TD>
            <TD>
              <Badge variant="accent">{row.channel}</Badge>
            </TD>
            <TD align="right">{formatDate(row.date)}</TD>
          </TRow>
        ))}
      </TBody>
    </Table>
  );
}
