import styles from "./Tooltip.module.css";

export default function Tooltip({
  content,
  children,
}: {
  content: string;
  children: React.ReactNode;
}) {
  return (
    <span className={styles.wrapper} tabIndex={0}>
      {children}
      <span className={styles.bubble} role="tooltip">
        {content}
      </span>
    </span>
  );
}
