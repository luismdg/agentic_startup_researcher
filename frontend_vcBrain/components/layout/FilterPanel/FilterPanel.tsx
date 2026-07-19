import styles from "./FilterPanel.module.css";

export default function FilterPanel({ children }: { children: React.ReactNode }) {
  return <div className={styles.panel}>{children}</div>;
}

export function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className={styles.group}>
      <span className={styles.label}>{label}</span>
      {children}
    </div>
  );
}
