import type { Founder } from "@/lib/types";
import { getStartup } from "@/lib/data";
import { Section } from "@/components/layout/SectionLayout/SectionLayout";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import TrendArrow from "@/components/ui/TrendArrow/TrendArrow";
import Badge from "@/components/ui/Badge/Badge";
import Monogram from "./Monogram";
import FounderTimeline from "./FounderTimeline";
import styles from "./FounderScoreCard.module.css";

export default function FounderScoreCard({ founder }: { founder: Founder }) {
  const startup = getStartup(founder.currentStartupId);

  return (
    <div className={styles.wrapper}>
      <header className={styles.header}>
        <Monogram initials={founder.initials} size="lg" />
        <div className={styles.headerInfo}>
          <h2 className={styles.name}>{founder.name}</h2>
          <div className={styles.metaRow}>
            <span>{founder.location}</span>
            <span className={styles.dot}>·</span>
            <span>{founder.archetype}</span>
            {founder.firstTimeFounder && <Badge variant="info">First-time</Badge>}
          </div>
          {startup && (
            <div className={styles.startup}>
              Currently building <span className={styles.startupName}>{startup.name}</span>
            </div>
          )}
        </div>
        <div className={styles.scoreBlock}>
          <div className={styles.scoreValue}>{founder.founderScore}</div>
          <TrendArrow trend={founder.founderScoreTrend} />
          <span className={styles.scoreHint}>Follows the person, not the company</span>
        </div>
      </header>

      <Section title="About them">
        <p className={styles.bio}>{founder.bio}</p>
      </Section>

      <Section title="What they built before">
        {founder.priorVentures.length === 0 ? (
          <EmptyState
            icon="sprout"
            title="This is their first company"
            description="No prior ventures — this founder is just getting started."
          />
        ) : (
          <ul className={styles.ventures}>
            {founder.priorVentures.map((venture) => (
              <li key={venture.name} className={styles.venture}>
                <div className={styles.ventureHead}>
                  <span className={styles.ventureName}>{venture.name}</span>
                  <span className={styles.ventureYears}>
                    {venture.yearStart}–{venture.yearEnd ?? "Present"}
                  </span>
                </div>
                <div className={styles.ventureRole}>{venture.role}</div>
                <div className={styles.ventureOutcome}>{venture.outcome}</div>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Timeline">
        <FounderTimeline events={founder.timeline} />
      </Section>
    </div>
  );
}
