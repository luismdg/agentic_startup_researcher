import type { Memo } from "@/lib/types";
import ConfidenceMeter from "@/components/ui/ConfidenceMeter/ConfidenceMeter";
import ScoreBar from "@/components/ui/ScoreBar/ScoreBar";
import Icon from "@/components/ui/Icon/Icon";
import styles from "./PortfolioFitCheck.module.css";

interface PortfolioFitCheckProps {
  portfolioFit: Memo["decision"]["portfolioFit"];
}

export default function PortfolioFitCheck({ portfolioFit }: PortfolioFitCheckProps) {
  return (
    <div className={styles.wrapper}>
      <h2 className={styles.heading}>
        <Icon name="link" size={18} /> Does It Fit What We Already Own?
      </h2>
      <p className={styles.subheading}>How this sits next to the rest of our portfolio — a separate read from the case above.</p>

      <div className={styles.block}>
        <span className={styles.label}>Companies we already have like this</span>
        {portfolioFit.overlapWith.length === 0 ? (
          <p className={styles.text}>None — this would be something new for us.</p>
        ) : (
          <ul className={styles.overlapList}>
            {portfolioFit.overlapWith.map((name) => (
              <li key={name} className={styles.overlapItem}>
                {name}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.block}>
        <span className={styles.label}>How it spreads out our bets</span>
        <p className={styles.text}>{portfolioFit.diversificationNote}</p>
      </div>

      <div className={styles.metrics}>
        <div className={styles.metric}>
          <span className={styles.label}>Risk of too much overlap</span>
          <ConfidenceMeter level={portfolioFit.concentrationRisk} />
        </div>
        <div className={styles.metric}>
          <span className={styles.label}>How well it fits</span>
          <ScoreBar score={portfolioFit.fitScore} />
        </div>
      </div>
    </div>
  );
}
