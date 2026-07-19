import styles from "./Table.module.css";

export function Table({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={styles.wrapper}>
      <table className={[styles.table, className].filter(Boolean).join(" ")}>{children}</table>
    </div>
  );
}

export function THead({ children }: { children: React.ReactNode }) {
  return <thead className={styles.thead}>{children}</thead>;
}

export function TBody({ children }: { children: React.ReactNode }) {
  return <tbody>{children}</tbody>;
}

export function TRow({
  children,
  onClick,
  active,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  active?: boolean;
}) {
  const classes = [styles.row, onClick ? styles.clickable : "", active ? styles.active : ""]
    .filter(Boolean)
    .join(" ");
  return (
    <tr className={classes} onClick={onClick}>
      {children}
    </tr>
  );
}

export function TH({ children, align }: { children: React.ReactNode; align?: "left" | "right" | "center" }) {
  return <th className={styles.th} style={{ textAlign: align ?? "left" }}>{children}</th>;
}

export function TD({ children, align }: { children: React.ReactNode; align?: "left" | "right" | "center" }) {
  return <td className={styles.td} style={{ textAlign: align ?? "left" }}>{children}</td>;
}
