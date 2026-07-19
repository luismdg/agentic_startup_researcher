"use client";

import { useState } from "react";
import type { RiskAppetite, ThesisPreset } from "@/lib/types";
import Select from "@/components/ui/Select/Select";
import Input from "@/components/ui/Input/Input";
import Button from "@/components/ui/Button/Button";
import ToggleChipGroup from "@/components/ui/ToggleChipGroup/ToggleChipGroup";
import Icon from "@/components/ui/Icon/Icon";
import styles from "./ThesisForm.module.css";

const RISK_OPTIONS = [
  { value: "conservative", label: "Careful — steady, lower-risk bets" },
  { value: "balanced", label: "Balanced — a bit of both" },
  { value: "aggressive", label: "Bold — big swings, big risk" },
];

interface ThesisFormProps {
  preset: ThesisPreset;
  sectorOptions: string[];
  stageOptions: string[];
  geographyOptions: string[];
}

function toArray(list: string[]): string {
  if (list.length === 0) return "anything";
  if (list.length === 1) return list[0];
  if (list.length === 2) return `${list[0]} and ${list[1]}`;
  return `${list.slice(0, -1).join(", ")}, and ${list[list.length - 1]}`;
}

function sameSet(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  const sortedA = [...a].sort();
  const sortedB = [...b].sort();
  return sortedA.every((v, i) => v === sortedB[i]);
}

export default function ThesisForm({ preset, sectorOptions, stageOptions, geographyOptions }: ThesisFormProps) {
  const [sectors, setSectors] = useState<string[]>(preset.sectors);
  const [stages, setStages] = useState<string[]>(preset.stages);
  const [geographies, setGeographies] = useState<string[]>(preset.geographies);
  const [checkSizeMin, setCheckSizeMin] = useState(preset.checkSizeMin);
  const [checkSizeMax, setCheckSizeMax] = useState(preset.checkSizeMax);
  const [ownershipTarget, setOwnershipTarget] = useState(preset.ownershipTarget);
  const [riskAppetite, setRiskAppetite] = useState<RiskAppetite>(preset.riskAppetite);
  const [saved, setSaved] = useState(false);

  const isDirty =
    !sameSet(sectors, preset.sectors) ||
    !sameSet(stages, preset.stages) ||
    !sameSet(geographies, preset.geographies) ||
    checkSizeMin !== preset.checkSizeMin ||
    checkSizeMax !== preset.checkSizeMax ||
    ownershipTarget !== preset.ownershipTarget ||
    riskAppetite !== preset.riskAppetite;

  function reset() {
    setSectors(preset.sectors);
    setStages(preset.stages);
    setGeographies(preset.geographies);
    setCheckSizeMin(preset.checkSizeMin);
    setCheckSizeMax(preset.checkSizeMax);
    setOwnershipTarget(preset.ownershipTarget);
    setRiskAppetite(preset.riskAppetite);
    setSaved(false);
  }

  const riskWord =
    riskAppetite === "conservative" ? "careful" : riskAppetite === "aggressive" ? "bold" : "balanced";

  return (
    <form
      className={styles.form}
      onSubmit={(e) => {
        e.preventDefault();
        setSaved(true);
      }}
    >
      <div className={styles.formHead}>
        <h2 className={styles.title}>{preset.name}</h2>
        <p className={styles.description}>{preset.description}</p>
      </div>

      <p className={styles.summary}>
        In plain English: you want <strong>{toArray(sectors)}</strong> startups, at the{" "}
        <strong>{toArray(stages)}</strong> stage, in <strong>{toArray(geographies)}</strong>. You&rsquo;d write
        checks between <strong>${Math.round(checkSizeMin / 1000)}K and ${Math.round(checkSizeMax / 1000)}K</strong>,
        aiming to own about <strong>{ownershipTarget}%</strong> of the company, and you&rsquo;re{" "}
        <strong>{riskWord}</strong> about risk.
      </p>

      <div className={styles.fieldset}>
        <span className={styles.legend}>What industries are you into?</span>
        <ToggleChipGroup
          options={sectorOptions.map((s) => ({ value: s, label: s }))}
          selected={sectors}
          onChange={(v) => {
            setSectors(v);
            setSaved(false);
          }}
          aria-label="Industries"
        />
      </div>

      <div className={styles.fieldset}>
        <span className={styles.legend}>How early or late-stage?</span>
        <ToggleChipGroup
          options={stageOptions.map((s) => ({ value: s, label: s }))}
          selected={stages}
          onChange={(v) => {
            setStages(v);
            setSaved(false);
          }}
          aria-label="Stages"
        />
      </div>

      <div className={styles.fieldset}>
        <span className={styles.legend}>Where in the world?</span>
        <ToggleChipGroup
          options={geographyOptions.map((g) => ({ value: g, label: g }))}
          selected={geographies}
          onChange={(v) => {
            setGeographies(v);
            setSaved(false);
          }}
          aria-label="Geographies"
        />
      </div>

      <div className={styles.numRow}>
        <label className={styles.numField}>
          <span className={styles.legend}>Smallest check you&rsquo;d write ($K)</span>
          <Input
            type="number"
            min={0}
            step={5}
            value={Math.round(checkSizeMin / 1000)}
            onChange={(e) => {
              setCheckSizeMin(Number(e.target.value) * 1000);
              setSaved(false);
            }}
          />
        </label>
        <label className={styles.numField}>
          <span className={styles.legend}>Largest check you&rsquo;d write ($K)</span>
          <Input
            type="number"
            min={0}
            step={5}
            value={Math.round(checkSizeMax / 1000)}
            onChange={(e) => {
              setCheckSizeMax(Number(e.target.value) * 1000);
              setSaved(false);
            }}
          />
        </label>
        <label className={styles.numField}>
          <span className={styles.legend}>How big a slice of the company? (%)</span>
          <Input
            type="number"
            min={0}
            max={100}
            step={0.5}
            value={ownershipTarget}
            onChange={(e) => {
              setOwnershipTarget(Number(e.target.value));
              setSaved(false);
            }}
          />
        </label>
      </div>

      <div className={styles.fieldset}>
        <span className={styles.legend}>How much risk feels okay?</span>
        <Select
          value={riskAppetite}
          onChange={(v) => {
            setRiskAppetite(v as RiskAppetite);
            setSaved(false);
          }}
          options={RISK_OPTIONS}
          aria-label="Comfort with risk"
        />
      </div>

      <div className={styles.actions}>
        <Button type="button" variant="ghost" onClick={reset} disabled={!isDirty}>
          Start over from this preset
        </Button>
        <Button type="submit" variant="primary" disabled={!isDirty || saved}>
          {saved ? (
            <>
              <Icon name="check" size={14} /> Saved
            </>
          ) : (
            "Save my choices"
          )}
        </Button>
      </div>
      {isDirty && !saved && <p className={styles.hint}>Just a heads up — this is a demo, so nothing leaves your screen.</p>}
    </form>
  );
}
