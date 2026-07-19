import styles from "./SectionLayout.module.css";

export function SplitPanel({
  list,
  detail,
}: {
  list: React.ReactNode;
  detail: React.ReactNode;
}) {
  return (
    <div className={styles.split}>
      <div className={styles.listPane}>{list}</div>
      <div className={styles.detailPane}>{detail}</div>
    </div>
  );
}

export function Section({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <section className={styles.section}>
      {title && <h2 className={styles.sectionTitle}>{title}</h2>}
      {children}
    </section>
  );
}
