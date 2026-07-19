"use client";

import { useMemo, useState } from "react";
import type { Startup, ThesisAutoMapExample, ThesisPreset } from "@/lib/types";
import { Section } from "@/components/layout/SectionLayout/SectionLayout";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import Select from "@/components/ui/Select/Select";
import TiltCard from "@/components/ui/TiltCard/TiltCard";
import Badge from "@/components/ui/Badge/Badge";
import { formatCurrency } from "@/lib/data";
import ThesisForm from "./ThesisForm";
import AutoMapPreview from "./AutoMapPreview";
import styles from "./ThesisView.module.css";

interface ThesisViewProps {
  presets: ThesisPreset[];
  activePresetId: string;
  autoMapExamples: ThesisAutoMapExample[];
  investedStartups: Startup[];
}

export default function ThesisView({ presets, activePresetId, autoMapExamples, investedStartups }: ThesisViewProps) {
  const [selectedId, setSelectedId] = useState(activePresetId);

  const selectedPreset = useMemo(
    () => presets.find((p) => p.id === selectedId) ?? presets[0],
    [presets, selectedId]
  );

  const sectorOptions = useMemo(
    () => Array.from(new Set(presets.flatMap((p) => p.sectors))).sort(),
    [presets]
  );
  const stageOptions = useMemo(
    () => Array.from(new Set(presets.flatMap((p) => p.stages))).sort(),
    [presets]
  );
  const geographyOptions = useMemo(
    () => Array.from(new Set(presets.flatMap((p) => p.geographies))).sort(),
    [presets]
  );
  const presetOptions = useMemo(() => presets.map((p) => ({ value: p.id, label: p.name })), [presets]);

  return (
    <>
      <p className={styles.intro}>
        Pick a starting point below, then adjust it your way. Everything else in the app — the
        ranked list, who we go find, and so on — follows whatever you set here.
      </p>
      <div className={styles.layout}>
        <div className={styles.main}>
          <label className={styles.presetPicker}>
            <span className={styles.presetLabel}>Starting point</span>
            <Select
              value={selectedId}
              onChange={setSelectedId}
              options={presetOptions}
              aria-label="Choose a starting preset"
            />
          </label>
          {selectedPreset && (
            <ThesisForm
              key={selectedPreset.id}
              preset={selectedPreset}
              sectorOptions={sectorOptions}
              stageOptions={stageOptions}
              geographyOptions={geographyOptions}
            />
          )}
          <div className={styles.autoMapWrap}>
            <Section title="Or just type it in your own words">
              <AutoMapPreview examples={autoMapExamples} />
            </Section>
          </div>
        </div>

        <aside className={styles.rail}>
          <h2 className={styles.railTitle}>Invested</h2>
          {investedStartups.length === 0 ? (
            <EmptyState
              icon="tray"
              title="Nothing invested yet"
              description="Startups you've actually put money into show up here as cards."
            />
          ) : (
            <div className={styles.cards}>
              {investedStartups.map((s) => (
                <TiltCard key={s.id} className={styles.card} maxTilt={6}>
                  <div className={styles.cardHead}>
                    <span className={styles.cardName}>{s.name}</span>
                    <Badge variant="success">Invested</Badge>
                  </div>
                  <p className={styles.cardTagline}>{s.tagline}</p>
                  <div className={styles.cardMeta}>
                    <span>{s.sector}</span>
                    <span>{s.stage}</span>
                  </div>
                  <div className={styles.cardCheck}>{formatCurrency(s.proposedCheckSize)} check</div>
                </TiltCard>
              ))}
            </div>
          )}
        </aside>
      </div>
    </>
  );
}
