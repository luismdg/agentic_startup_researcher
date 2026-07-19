import { getActiveThesisPreset } from "@/lib/data";
import ThemeToggle from "@/components/layout/ThemeToggle/ThemeToggle";
import styles from "./TopBar.module.css";

export default function TopBar() {
  const preset = getActiveThesisPreset();

  return (
    <header className={styles.topbar}>
      <div className={styles.thesis}>
        <span className={styles.thesisLabel}>Active thesis</span>
        <span className={styles.thesisName}>{preset.name}</span>
      </div>
      <div className={styles.investor}>
        <ThemeToggle />
        <span className={styles.investorName}>Solo GP seat</span>
        <span className={styles.avatar}>SG</span>
      </div>
    </header>
  );
}
