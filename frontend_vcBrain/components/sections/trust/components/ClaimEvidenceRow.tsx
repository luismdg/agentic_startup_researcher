import type { TrustClaim } from "@/lib/types";
import { formatDate } from "@/lib/data";
import Badge from "@/components/ui/Badge/Badge";
import ConfidenceMeter from "@/components/ui/ConfidenceMeter/ConfidenceMeter";
import ExpandableRow from "@/components/layout/ExpandableRow/ExpandableRow";
import styles from "./ClaimEvidenceRow.module.css";

export default function ClaimEvidenceRow({ claim }: { claim: TrustClaim }) {
  const hasContradiction = claim.contradiction !== null;

  const summary = (
    <span className={styles.summaryContent}>
      <span className={styles.claimText}>{claim.claim}</span>
      {hasContradiction && <Badge variant="danger">Contradiction flagged</Badge>}
    </span>
  );

  const meta = <ConfidenceMeter level={claim.confidence} />;

  return (
    <div className={hasContradiction ? `${styles.wrapper} ${styles.contradicted}` : styles.wrapper}>
      <ExpandableRow summary={summary} meta={meta}>
        <dl className={styles.detailList}>
          <dt className={styles.detailLabel}>Source</dt>
          <dd className={styles.detailValue}>{claim.source}</dd>
          <dt className={styles.detailLabel}>Kind of proof</dt>
          <dd className={styles.detailValue}>{claim.evidenceType}</dd>
          <dt className={styles.detailLabel}>Verified</dt>
          <dd className={styles.detailValue}>{formatDate(claim.verifiedDate)}</dd>
        </dl>
        {claim.contradiction !== null && (
          <div className={styles.contradictionBlock}>
            <span className={styles.contradictionLabel}>Contradiction:</span>{" "}
            <span className={styles.contradictionText}>{claim.contradiction}</span>
          </div>
        )}
      </ExpandableRow>
    </div>
  );
}
