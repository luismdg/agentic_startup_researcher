import type { Startup, Memo } from "@/lib/types";
import HeadlineDecision from "./HeadlineDecision";
import AdversarialView from "./AdversarialView";
import PortfolioFitCheck from "./PortfolioFitCheck";
import styles from "./DecisionView.module.css";

interface DecisionViewProps {
  startup: Startup;
  decision: Memo["decision"];
}

export default function DecisionView({ startup, decision }: DecisionViewProps) {
  return (
    <div>
      <HeadlineDecision startup={startup} decision={decision} />
      <div className={styles.panels}>
        <div>
          <AdversarialView adversarialView={decision.adversarialView} />
        </div>
        <div className={styles.panelRight}>
          <PortfolioFitCheck portfolioFit={decision.portfolioFit} />
        </div>
      </div>
    </div>
  );
}
