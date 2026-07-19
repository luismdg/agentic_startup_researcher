import type { Memo } from "@/lib/types";
import { formatCurrency, formatDate } from "@/lib/data";
import { Table, THead, TBody, TRow, TH, TD } from "@/components/ui/Table/Table";
import MemoSection from "./MemoSection";
import MissingDataFlag from "./MissingDataFlag";
import StatGrid from "./StatGrid";
import SwotGrid from "./SwotGrid";
import { availableValue } from "./memoField";
import { buildSnapshotNarrative } from "./snapshotNarrative";
import styles from "./MemoDocument.module.css";

/**
 * Document-style, single-column rendering of a full investment memo.
 * `decision` is intentionally never read here — that belongs to the
 * Decision tab in /evaluate.
 */
export default function MemoDocument({ memo }: { memo: Memo }) {
  const { companySnapshot } = memo;

  const teamHistory = availableValue(memo.teamHistory);
  const technologyDefensibility = availableValue(memo.technologyDefensibility);
  const marketSizing = availableValue(memo.marketSizing);
  const competition = availableValue(memo.competition);
  const dueDiligenceLog = availableValue(memo.dueDiligenceLog);
  const financials = availableValue(memo.financials);
  const capTable = availableValue(memo.capTable);
  const exitPerspective = availableValue(memo.exitPerspective);

  return (
    <article className={styles.document}>
      <p className={styles.generatedLine}>Memo generated {formatDate(memo.generatedDate)}</p>

      <MemoSection title="The Basics">
        <StatGrid
          items={[
            { label: "Name", value: companySnapshot.name },
            { label: "Industry", value: companySnapshot.sector },
            { label: "Stage", value: companySnapshot.stage },
            { label: "Where", value: companySnapshot.geography },
            { label: "Founded", value: String(companySnapshot.foundedYear) },
            { label: "How much they want", value: formatCurrency(companySnapshot.askAmount) },
            { label: "How much we'd put in", value: formatCurrency(companySnapshot.proposedCheckSize) },
          ]}
        />
      </MemoSection>

      <MemoSection title="In a Nutshell">
        <p className={styles.prose}>{buildSnapshotNarrative(memo, marketSizing)}</p>
      </MemoSection>

      <MemoSection title="Why This Could Work">
        <ol className={styles.orderedList}>
          {memo.investmentHypotheses.map((hypothesis, i) => (
            <li key={i}>{hypothesis}</li>
          ))}
        </ol>
      </MemoSection>

      <MemoSection title="The Good, the Bad & the Risks">
        <SwotGrid swot={memo.swot} />
      </MemoSection>

      <MemoSection title="Problem & Product">
        <div className={styles.proseBlock}>
          <h3 className={styles.proseLabel}>The problem</h3>
          <p className={styles.prose}>{memo.problemProduct.problem}</p>
        </div>
        <div className={styles.proseBlock}>
          <h3 className={styles.proseLabel}>Their product</h3>
          <p className={styles.prose}>{memo.problemProduct.product}</p>
        </div>
      </MemoSection>

      <MemoSection title="How It's Doing So Far">
        <Table>
          <THead>
            <TRow>
              <TH>What we&rsquo;re tracking</TH>
              <TH>Where it stands</TH>
              <TH align="right">As of</TH>
            </TRow>
          </THead>
          <TBody>
            {memo.tractionKpis.map((kpi, i) => (
              <TRow key={`${kpi.label}-${i}`}>
                <TD>{kpi.label}</TD>
                <TD>{kpi.value}</TD>
                <TD align="right">{formatDate(kpi.asOf)}</TD>
              </TRow>
            ))}
          </TBody>
        </Table>
      </MemoSection>

      <MemoSection title="The Team">
        {teamHistory !== null ? (
          <p className={styles.prose}>{teamHistory}</p>
        ) : (
          <MissingDataFlag reason={memo.teamHistory.status} />
        )}
      </MemoSection>

      <MemoSection title="The Tech, and Why It's Hard to Copy">
        {technologyDefensibility !== null ? (
          <p className={styles.prose}>{technologyDefensibility}</p>
        ) : (
          <MissingDataFlag reason={memo.technologyDefensibility.status} />
        )}
      </MemoSection>

      <MemoSection title="How Big Is the Market?">
        {marketSizing !== null ? (
          <>
            <StatGrid
              items={[
                { label: "Everyone who could ever buy this", value: marketSizing.tam },
                { label: "The slice we could realistically sell to", value: marketSizing.sam },
                { label: "What we could actually capture", value: marketSizing.som },
              ]}
            />
            <p className={styles.prose}>{marketSizing.note}</p>
          </>
        ) : (
          <MissingDataFlag reason={memo.marketSizing.status} />
        )}
      </MemoSection>

      <MemoSection title="Who Else Is Doing This?">
        {competition !== null ? (
          <Table>
            <THead>
              <TRow>
                <TH>Competitor</TH>
                <TH>How they&rsquo;re different</TH>
              </TRow>
            </THead>
            <TBody>
              {competition.map((entry, i) => (
                <TRow key={`${entry.name}-${i}`}>
                  <TD>{entry.name}</TD>
                  <TD>{entry.positioning}</TD>
                </TRow>
              ))}
            </TBody>
          </Table>
        ) : (
          <MissingDataFlag reason={memo.competition.status} />
        )}
      </MemoSection>

      <MemoSection title="What We've Checked">
        {dueDiligenceLog !== null ? (
          <p className={styles.prose}>
            {dueDiligenceLog.verifiedCount} confirmed &middot; {dueDiligenceLog.openCount} still open &middot;{" "}
            {dueDiligenceLog.contradictedCount} didn&rsquo;t check out &mdash; last updated{" "}
            {formatDate(dueDiligenceLog.lastUpdated)}
          </p>
        ) : (
          <MissingDataFlag reason={memo.dueDiligenceLog.status} />
        )}
      </MemoSection>

      <MemoSection title="Money & Round Structure" flag="Not always shared">
        {financials !== null ? (
          <StatGrid
            items={[
              { label: "Yearly revenue", value: financials.arr },
              { label: "Monthly spend", value: financials.burnRate },
              { label: "Months of cash left", value: financials.runway },
            ]}
          />
        ) : (
          <MissingDataFlag reason={memo.financials.status} />
        )}
      </MemoSection>

      <MemoSection title="Who Owns What" flag="Not always shared">
        {capTable !== null ? (
          <Table>
            <THead>
              <TRow>
                <TH>Owner</TH>
                <TH align="right">Share</TH>
              </TRow>
            </THead>
            <TBody>
              {capTable.map((entry, i) => (
                <TRow key={`${entry.holder}-${i}`}>
                  <TD>{entry.holder}</TD>
                  <TD align="right">{entry.percent}%</TD>
                </TRow>
              ))}
            </TBody>
          </Table>
        ) : (
          <MissingDataFlag reason={memo.capTable.status} />
        )}
      </MemoSection>

      <MemoSection title="How This Could End" flag="Not always shared">
        {exitPerspective !== null ? (
          <p className={styles.prose}>{exitPerspective}</p>
        ) : (
          <MissingDataFlag reason={memo.exitPerspective.status} />
        )}
      </MemoSection>
    </article>
  );
}
