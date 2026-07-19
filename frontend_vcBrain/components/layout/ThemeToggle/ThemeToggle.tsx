"use client";

import Icon from "@/components/ui/Icon/Icon";
import styles from "./ThemeToggle.module.css";

const STORAGE_KEY = "vc-brain-theme";

export default function ThemeToggle() {
  function toggle() {
    const root = document.documentElement;
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    window.localStorage.setItem(STORAGE_KEY, next);
  }

  return (
    <button
      type="button"
      className={styles.toggle}
      onClick={toggle}
      aria-label="Toggle color theme"
      title="Toggle color theme"
    >
      <span className={`${styles.icon} ${styles.iconLight}`}>
        <Icon name="moon" size={15} />
      </span>
      <span className={`${styles.icon} ${styles.iconDark}`}>
        <Icon name="sun" size={15} />
      </span>
    </button>
  );
}
