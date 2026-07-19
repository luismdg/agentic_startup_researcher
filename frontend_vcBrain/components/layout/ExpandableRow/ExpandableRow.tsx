"use client";

import { useState } from "react";
import Icon from "@/components/ui/Icon/Icon";
import styles from "./ExpandableRow.module.css";

interface ExpandableRowProps {
  summary: React.ReactNode;
  meta?: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export default function ExpandableRow({ summary, meta, children, defaultOpen = false }: ExpandableRowProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={styles.row}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className={`${styles.caret} ${open ? styles.caretOpen : ""}`}>
          <Icon name="chevronRight" size={13} />
        </span>
        <span className={styles.summary}>{summary}</span>
        {meta && <span className={styles.meta}>{meta}</span>}
      </button>
      {open && <div className={styles.panel}>{children}</div>}
    </div>
  );
}
