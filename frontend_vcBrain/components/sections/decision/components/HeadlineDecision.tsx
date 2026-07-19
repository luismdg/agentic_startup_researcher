import type { Startup, Memo } from "@/lib/types";
import Badge from "@/components/ui/Badge/Badge";
import { formatCurrency, formatDate } from "@/lib/data";
import styles from "./HeadlineDecision.module.css";

type Recommendation = Memo["decision"]["recommendation"];

const RECOMMENDATION_LABEL: Record<Recommendation, string> = {
  invest: "Invest",
  pass: "Pass",
  watch: "Watch",
};

interface HeadlineDecisionProps {
  startup: Startup;
  decision: Memo["decision"];
}

export default function HeadlineDecision({ startup, decision }: HeadlineDecisionProps) {
  return (
    <div className={styles.headline}>
      <div className={styles.top}>
        <div>
          <span className={styles.eyebrow}>{startup.name} — final call</span>
          <div className={`${styles.recommendation} ${styles[decision.recommendation]}`}>
            {RECOMMENDATION_LABEL[decision.recommendation]}
          </div>
        </div>
        <div className={styles.meta}>
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>How much we&rsquo;d invest</span>
            <span className={styles.checkValue}>{formatCurrency(decision.checkSize)}</span>
          </div>
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Status</span>
            <Badge variant={decision.decidedDate ? "neutral" : "warning"}>
              {decision.decidedDate ? `Decided on ${formatDate(decision.decidedDate)}` : "Decision pending"}
            </Badge>
          </div>
        </div>
      </div>
      <p className={styles.rationale}>{decision.rationale}</p>
    </div>
  );
}
