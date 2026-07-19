import styles from "./Badge.module.css";

export type BadgeVariant = "neutral" | "success" | "warning" | "danger" | "info" | "accent";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
}

export default function Badge({ children, variant = "neutral" }: BadgeProps) {
  return <span className={`${styles.badge} ${styles[variant]}`}>{children}</span>;
}
