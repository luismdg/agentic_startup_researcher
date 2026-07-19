"use client";

import { useState } from "react";
import Button from "@/components/ui/Button/Button";
import Input from "@/components/ui/Input/Input";
import Icon, { type IconName } from "@/components/ui/Icon/Icon";
import styles from "./GuidedFilterGate.module.css";

interface GuidedFilterGateProps {
  icon?: IconName;
  eyebrow?: string;
  title: string;
  description: string;
  children?: React.ReactNode;
  onApply: () => void;
  applied: boolean;
  summary?: React.ReactNode;
  actionLabel?: string;
  keyword?: string;
  onKeywordChange?: (value: string) => void;
  keywordPlaceholder?: string;
}

export default function GuidedFilterGate({
  icon = "search",
  eyebrow = "Let's find what you want",
  title,
  description,
  children,
  onApply,
  applied,
  summary,
  actionLabel = "Show results",
  keyword,
  onKeywordChange,
  keywordPlaceholder = "Type anything — a name, word, or idea…",
}: GuidedFilterGateProps) {
  const [expanded, setExpanded] = useState(!applied);

  function handleApply() {
    onApply();
    setExpanded(false);
  }

  if (applied && !expanded) {
    return (
      <div className={styles.collapsed}>
        <div className={styles.collapsedSummary}>
          <span className={styles.collapsedLabel}>
            <Icon name={icon} size={14} /> {eyebrow}
          </span>
          <div className={styles.summaryContent}>{summary}</div>
        </div>
        <Button variant="ghost" onClick={() => setExpanded(true)}>
          Change my search
        </Button>
      </div>
    );
  }

  return (
    <div className={styles.gate}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>
          <Icon name={icon} size={14} /> {eyebrow}
        </span>
        <h2 className={styles.title}>{title}</h2>
        <p className={styles.description}>{description}</p>
      </div>
      {onKeywordChange && (
        <div className={styles.keywordRow}>
          <Input
            value={keyword ?? ""}
            onChange={(e) => onKeywordChange(e.target.value)}
            placeholder={keywordPlaceholder}
            aria-label="Search by keyword"
            className={styles.keywordInput}
          />
        </div>
      )}
      {children && <div className={styles.criteria}>{children}</div>}
      <div className={styles.actions}>
        <Button variant="primary" onClick={handleApply}>
          {actionLabel}
        </Button>
        {applied && (
          <Button variant="ghost" onClick={() => setExpanded(false)}>
            Never mind
          </Button>
        )}
      </div>
    </div>
  );
}
