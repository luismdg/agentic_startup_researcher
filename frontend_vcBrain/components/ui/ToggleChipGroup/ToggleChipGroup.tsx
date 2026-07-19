"use client";

import styles from "./ToggleChipGroup.module.css";

interface ChipOption {
  value: string;
  label: string;
}

interface ToggleChipGroupProps {
  options: ChipOption[];
  selected: string[];
  onChange: (values: string[]) => void;
  "aria-label"?: string;
}

export default function ToggleChipGroup({
  options,
  selected,
  onChange,
  ...rest
}: ToggleChipGroupProps) {
  function toggle(value: string) {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  }

  return (
    <div className={styles.group} role="group" {...rest}>
      {options.map((opt) => {
        const active = selected.includes(opt.value);
        return (
          <button
            key={opt.value}
            type="button"
            className={`${styles.chip} ${active ? styles.active : ""}`}
            aria-pressed={active}
            onClick={() => toggle(opt.value)}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
