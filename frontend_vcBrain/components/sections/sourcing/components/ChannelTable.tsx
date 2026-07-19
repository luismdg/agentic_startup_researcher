import type { SourcingChannel } from "@/lib/types";
import { formatDate } from "@/lib/data";
import { Table, THead, TBody, TRow, TH, TD } from "@/components/ui/Table/Table";
import Badge from "@/components/ui/Badge/Badge";
import ScoreBar from "@/components/ui/ScoreBar/ScoreBar";
import styles from "./ChannelTable.module.css";

const TYPE_LABEL: Record<SourcingChannel["type"], string> = {
  accelerator: "Accelerator",
  hackathon: "Hackathon",
  github: "GitHub",
  research: "Research",
  community: "Community",
  web: "Google / Web",
};

export default function ChannelTable({ channels }: { channels: SourcingChannel[] }) {
  const sorted = [...channels].sort((a, b) => b.totalSourced - a.totalSourced);

  return (
    <Table>
      <THead>
        <tr>
          <TH>Channel</TH>
          <TH>Type</TH>
          <TH>Region</TH>
          <TH align="right">Active deals</TH>
          <TH align="right">Total sourced</TH>
          <TH align="right">Conversion</TH>
          <TH>Quality score</TH>
          <TH>Last signal</TH>
        </tr>
      </THead>
      <TBody>
        {sorted.map((c) => (
          <TRow key={c.id}>
            <TD>
              <div className={styles.name}>{c.name}</div>
              <div className={styles.notes}>{c.notes}</div>
            </TD>
            <TD>
              <Badge variant="neutral">{TYPE_LABEL[c.type]}</Badge>
            </TD>
            <TD>{c.region}</TD>
            <TD align="right">{c.activeDeals}</TD>
            <TD align="right">{c.totalSourced}</TD>
            <TD align="right">{Math.round(c.conversionRate * 100)}%</TD>
            <TD>
              <ScoreBar score={c.qualityScore} />
            </TD>
            <TD>{formatDate(c.lastSignalDate)}</TD>
          </TRow>
        ))}
      </TBody>
    </Table>
  );
}
