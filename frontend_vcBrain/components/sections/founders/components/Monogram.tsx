import styles from "./Monogram.module.css";

interface MonogramProps {
  initials: string;
  size?: "sm" | "md" | "lg";
}

export default function Monogram({ initials, size = "md" }: MonogramProps) {
  return <span className={`${styles.monogram} ${styles[size]}`}>{initials}</span>;
}
