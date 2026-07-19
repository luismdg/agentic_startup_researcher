"use client";

import { useRouter } from "next/navigation";
import type { Startup } from "@/lib/types";
import Select from "@/components/ui/Select/Select";
import styles from "./StartupSwitcher.module.css";

interface StartupSwitcherProps {
  startups: Startup[];
  currentId: string;
  basePath: string;
}

export default function StartupSwitcher({ startups, currentId, basePath }: StartupSwitcherProps) {
  const router = useRouter();

  const options = startups.map((s) => ({
    value: s.id,
    label: `${s.name} — ${s.sector}`,
  }));

  return (
    <div className={styles.switcher}>
      <span className={styles.label}>Opportunity</span>
      <Select
        value={currentId}
        onChange={(id) => router.push(`${basePath}?startup=${id}`)}
        options={options}
        aria-label="Select opportunity"
      />
    </div>
  );
}
