"use client";

import { useMemo, useState } from "react";
import type { DiligenceLogEntry, DiligenceStatus } from "@/lib/types";
import FilterPanel, { FilterGroup } from "@/components/layout/FilterPanel/FilterPanel";
import { Section } from "@/components/layout/SectionLayout/SectionLayout";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import Select from "@/components/ui/Select/Select";
import Input from "@/components/ui/Input/Input";
import GapLogEntry from "./GapLogEntry";
import styles from "./DiligenceLogView.module.css";

const CATEGORY_ORDER = ["Team", "Market", "Product", "Financial", "Legal", "Technical"];

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: "verified", label: "Verified" },
  { value: "open", label: "Open" },
  { value: "contradicted", label: "Contradicted" },
];

function orderCategories(keys: string[]): string[] {
  return [
    ...CATEGORY_ORDER.filter((c) => keys.includes(c)),
    ...keys.filter((c) => !CATEGORY_ORDER.includes(c)).sort(),
  ];
}

export default function DiligenceLogView({ entries }: { entries: DiligenceLogEntry[] }) {
  const [category, setCategory] = useState("all");
  const [status, setStatus] = useState("all");
  const [keyword, setKeyword] = useState("");

  const categoryOptions = useMemo(() => {
    const present = Array.from(new Set(entries.map((e) => e.category)));
    return [
      { value: "all", label: "All categories" },
      ...orderCategories(present).map((c) => ({ value: c, label: c })),
    ];
  }, [entries]);

  const rollup = useMemo(() => {
    const counts: Record<DiligenceStatus, number> = { verified: 0, open: 0, contradicted: 0 };
    entries.forEach((e) => {
      counts[e.status] += 1;
    });
    return counts;
  }, [entries]);

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    return entries.filter((e) => {
      if (category !== "all" && e.category !== category) return false;
      if (status !== "all" && e.status !== status) return false;
      if (q) {
        const haystack = [e.item, e.notes, e.owner].join(" ").toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [entries, category, status, keyword]);

  const grouped = useMemo(() => {
    const byCategory = new Map<string, DiligenceLogEntry[]>();
    filtered.forEach((e) => {
      const list = byCategory.get(e.category) ?? [];
      list.push(e);
      byCategory.set(e.category, list);
    });
    byCategory.forEach((list) => list.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0)));
    return orderCategories(Array.from(byCategory.keys())).map((key) => ({
      category: key,
      items: byCategory.get(key) as DiligenceLogEntry[],
    }));
  }, [filtered]);

  return (
    <>
      <p className={styles.rollup}>
        <span className={styles.verified}>{rollup.verified} verified</span>
        <span className={styles.dot} aria-hidden="true">
          ·
        </span>
        <span className={styles.open}>{rollup.open} open</span>
        <span className={styles.dot} aria-hidden="true">
          ·
        </span>
        <span className={styles.contradicted}>{rollup.contradicted} contradicted</span>
      </p>

      <FilterPanel>
        <FilterGroup label="Search">
          <Input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Search this checklist…"
            aria-label="Search checklist entries"
          />
        </FilterGroup>
        <FilterGroup label="Category">
          <Select
            value={category}
            onChange={setCategory}
            options={categoryOptions}
            aria-label="Filter by category"
          />
        </FilterGroup>
        <FilterGroup label="Status">
          <Select value={status} onChange={setStatus} options={STATUS_OPTIONS} aria-label="Filter by status" />
        </FilterGroup>
      </FilterPanel>

      {grouped.length === 0 ? (
        <EmptyState
          icon="checklist"
          title="Nothing matches those filters"
          description="Try a different category or status to see more of the checklist."
        />
      ) : (
        grouped.map((group) => (
          <Section key={group.category} title={group.category}>
            <div className={styles.list}>
              {group.items.map((entry) => (
                <GapLogEntry key={entry.id} entry={entry} />
              ))}
            </div>
          </Section>
        ))
      )}
    </>
  );
}
