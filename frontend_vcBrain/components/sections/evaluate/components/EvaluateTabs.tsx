"use client";

import type { ReactNode } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Tabs from "@/components/ui/Tabs/Tabs";
import styles from "./EvaluateTabs.module.css";

export type EvaluateTab = "scorecard" | "checklist" | "report" | "decision";

const TAB_OPTIONS: { value: EvaluateTab; label: string }[] = [
  { value: "scorecard", label: "Scorecard" },
  { value: "checklist", label: "Checklist" },
  { value: "report", label: "Report" },
  { value: "decision", label: "Decision" },
];

interface EvaluateTabsProps {
  startupId: string;
  activeTab: EvaluateTab;
  panels: Record<EvaluateTab, ReactNode>;
}

/**
 * All 4 panels are already server-fetched by app/evaluate/page.tsx and
 * passed in as ready-made nodes -- switching tabs here is pure client-side
 * visibility toggling, no extra fetch per tab. The active tab lives in the
 * URL (?tab=) so it's linkable/shareable, same as every other basePath-driven
 * navigation in this app (StartupSwitcher, OpportunityGate).
 */
export default function EvaluateTabs({ startupId, activeTab, panels }: EvaluateTabsProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleChange(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("startup", startupId);
    params.set("tab", value);
    router.push(`/evaluate?${params.toString()}`);
  }

  return (
    <div>
      <Tabs tabs={TAB_OPTIONS} value={activeTab} onChange={handleChange} />
      <div className={styles.panel}>{panels[activeTab]}</div>
    </div>
  );
}
