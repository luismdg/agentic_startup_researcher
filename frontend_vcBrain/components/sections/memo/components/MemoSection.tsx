import { Section } from "@/components/layout/SectionLayout/SectionLayout";
import Badge from "@/components/ui/Badge/Badge";
import styles from "./MemoSection.module.css";

/**
 * A titled block of the memo document. Composes the shared Section heading
 * with a thin bottom divider so consecutive memo sections read as a linear
 * document rather than stacked cards. An optional `flag` renders a small
 * badge next to the title (e.g. to mark a section as sensitive/optional)
 * without merging it into any other section.
 */
export default function MemoSection({
  title,
  flag,
  children,
}: {
  title: string;
  flag?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={styles.wrapper}>
      <Section>
        <div className={styles.heading}>
          <h2 className={styles.title}>{title}</h2>
          {flag && <Badge variant="neutral">{flag}</Badge>}
        </div>
        {children}
      </Section>
    </div>
  );
}
