import type { TrustClaim, Confidence } from "@/lib/types";
import ClaimEvidenceRow from "./ClaimEvidenceRow";
import styles from "./TrustClaimsList.module.css";

const CONFIDENCE_RANK: Record<Confidence, number> = { high: 3, medium: 2, low: 1 };

export default function TrustClaimsList({ claims }: { claims: TrustClaim[] }) {
  if (claims.length === 0) {
    return <p className={styles.empty}>No claims on file for this opportunity.</p>;
  }

  const sorted = [...claims].sort((a, b) => {
    const aFlag = a.contradiction !== null ? 1 : 0;
    const bFlag = b.contradiction !== null ? 1 : 0;
    if (aFlag !== bFlag) return bFlag - aFlag;
    return CONFIDENCE_RANK[b.confidence] - CONFIDENCE_RANK[a.confidence];
  });

  const contradictedCount = claims.filter((c) => c.contradiction !== null).length;
  const highCount = claims.filter((c) => c.confidence === "high").length;
  const mediumCount = claims.filter((c) => c.confidence === "medium").length;
  const lowCount = claims.filter((c) => c.confidence === "low").length;

  return (
    <div>
      <div className={styles.rollup}>
        <span className={styles.rollupItem}>
          <span
            className={
              contradictedCount > 0
                ? `${styles.rollupValue} ${styles.rollupValueDanger}`
                : styles.rollupValue
            }
          >
            {contradictedCount}
          </span>{" "}
          of <span className={styles.rollupValue}>{claims.length}</span> claims contradicted
        </span>
        <span className={styles.rollupItem}>
          <span className={styles.rollupValue}>{highCount}</span> high confidence
        </span>
        <span className={styles.rollupItem}>
          <span className={styles.rollupValue}>{mediumCount}</span> medium confidence
        </span>
        <span className={styles.rollupItem}>
          <span className={styles.rollupValue}>{lowCount}</span> low confidence
        </span>
      </div>
      <div className={styles.listContainer}>
        {sorted.map((claim) => (
          <ClaimEvidenceRow key={claim.id} claim={claim} />
        ))}
      </div>
    </div>
  );
}
