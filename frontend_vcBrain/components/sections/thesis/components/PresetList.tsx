"use client";

import type { RiskAppetite, ThesisPreset } from "@/lib/types";
import type { BadgeVariant } from "@/components/ui/Badge/Badge";
import Badge from "@/components/ui/Badge/Badge";
import styles from "./PresetList.module.css";

const RISK_VARIANT: Record<RiskAppetite, BadgeVariant> = {
  conservative: "success",
  balanced: "warning",
  aggressive: "danger",
};

const RISK_LABEL: Record<RiskAppetite, string> = {
  conservative: "Careful",
  balanced: "Balanced",
  aggressive: "Bold",
};

interface PresetListProps {
  presets: ThesisPreset[];
  activeId: string;
  onSelect: (id: string) => void;
}

export default function PresetList({ presets, activeId, onSelect }: PresetListProps) {
  return (
    <ul className={styles.list}>
      {presets.map((preset) => {
        const isActive = preset.id === activeId;
        return (
          <li key={preset.id} className={styles.item}>
            <div
              role="button"
              tabIndex={0}
              className={`${styles.row} ${isActive ? styles.active : ""}`}
              onClick={() => onSelect(preset.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect(preset.id);
                }
              }}
              aria-pressed={isActive}
            >
              <div className={styles.rowHead}>
                <span className={styles.name}>{preset.name}</span>
                <Badge variant={RISK_VARIANT[preset.riskAppetite]}>
                  {RISK_LABEL[preset.riskAppetite]}
                </Badge>
              </div>
              <p className={styles.description}>{preset.description}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
