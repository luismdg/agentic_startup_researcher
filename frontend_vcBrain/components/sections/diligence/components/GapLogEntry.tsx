import type { DiligenceLogEntry, DiligenceStatus } from "@/lib/types";
import { formatDate } from "@/lib/data";
import ExpandableRow from "@/components/layout/ExpandableRow/ExpandableRow";
import Badge, { type BadgeVariant } from "@/components/ui/Badge/Badge";
import styles from "./GapLogEntry.module.css";

const STATUS_VARIANT: Record<DiligenceStatus, BadgeVariant> = {
  verified: "success",
  open: "warning",
  contradicted: "danger",
};

const STATUS_LABEL: Record<DiligenceStatus, string> = {
  verified: "Verified",
  open: "Open",
  contradicted: "Contradicted",
};

export default function GapLogEntry({ entry }: { entry: DiligenceLogEntry }) {
  return (
    <ExpandableRow
      summary={entry.item}
      meta={
        <>
          <Badge variant={STATUS_VARIANT[entry.status]}>{STATUS_LABEL[entry.status]}</Badge>
          <span className={styles.date}>{formatDate(entry.date)}</span>
        </>
      }
    >
      <div className={styles.details}>
        <div className={styles.detailRow}>
          <span className={styles.detailLabel}>Category</span>
          <span className={styles.detailValue}>{entry.category}</span>
        </div>
        <div className={styles.detailRow}>
          <span className={styles.detailLabel}>Owner</span>
          <span className={styles.detailValue}>{entry.owner}</span>
        </div>
      </div>
      <p className={styles.notes}>{entry.notes}</p>
    </ExpandableRow>
  );
}
