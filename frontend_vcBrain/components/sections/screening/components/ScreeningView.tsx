import type { Screening, Startup } from "@/lib/types";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import AxisScoreColumn from "./AxisScoreColumn";
import AxisTrendChart from "./AxisTrendChart";
import styles from "./ScreeningView.module.css";

interface ScreeningViewProps {
  startup: Startup;
  screening?: Screening;
}

/**
 * Orchestrates the multi-axis screening view for a single selected startup.
 * The three axes (founder / market / idea-market-fit) are rendered as
 * separate, non-averaged columns — no combined score is ever computed here.
 * Startup identity (name/sector/stage) is shown once by the Evaluate
 * section's shared EvaluateHeader, not repeated here.
 */
export default function ScreeningView({ screening }: ScreeningViewProps) {
  return (
    <div>
      {!screening ? (
        <EmptyState
          icon="scorecard"
          title="No scorecard yet"
          description="We haven't scored this startup yet."
        />
      ) : (
        <>
          <div className={styles.columns}>
            <AxisScoreColumn label="The People" colorVar="var(--color-axis-founder)" data={screening.founder} />
            <AxisScoreColumn label="The Market" colorVar="var(--color-axis-market)" data={screening.market} />
            <AxisScoreColumn
              label="Does the Idea Fit?"
              colorVar="var(--color-axis-idea)"
              data={screening.ideaMarketFit}
            />
          </div>

          <div className={styles.chartSection}>
            <h2 className={styles.chartTitle}>How each has changed, month by month</h2>
            <AxisTrendChart history={screening.history} />
          </div>
        </>
      )}
    </div>
  );
}
