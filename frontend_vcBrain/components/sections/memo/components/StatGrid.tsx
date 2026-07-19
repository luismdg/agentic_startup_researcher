import styles from "./StatGrid.module.css";

export interface Stat {
  label: string;
  value: string;
}

/**
 * Compact labeled key-value grid used for the company snapshot, market
 * sizing (TAM/SAM/SOM) and financials (ARR/burn/runway) stats. Plain inline
 * text pairs, not boxed stat tiles.
 */
export default function StatGrid({ items }: { items: Stat[] }) {
  return (
    <dl className={styles.grid}>
      {items.map((item) => (
        <div className={styles.item} key={item.label}>
          <dt className={styles.label}>{item.label}</dt>
          <dd className={styles.value}>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
