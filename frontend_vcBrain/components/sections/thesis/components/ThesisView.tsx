"use client";

import { useMemo, useState } from "react";
import type { ThesisAutoMapExample, ThesisPreset } from "@/lib/types";
import { SplitPanel, Section } from "@/components/layout/SectionLayout/SectionLayout";
import PresetList from "./PresetList";
import ThesisForm from "./ThesisForm";
import AutoMapPreview from "./AutoMapPreview";
import styles from "./ThesisView.module.css";

interface ThesisViewProps {
  presets: ThesisPreset[];
  activePresetId: string;
  autoMapExamples: ThesisAutoMapExample[];
}

export default function ThesisView({ presets, activePresetId, autoMapExamples }: ThesisViewProps) {
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

  return (
    <>
      <p className={styles.intro}>
        Pick one of your saved starting points on the left, then adjust it on the right. Everything
        else in the app — the ranked list, who we go find, and so on — follows whatever you set here.
      </p>
      <SplitPanel
        list={<PresetList presets={presets} activeId={selectedId} onSelect={setSelectedId} />}
        detail={
          selectedPreset ? (
            <ThesisForm
              key={selectedPreset.id}
              preset={selectedPreset}
              sectorOptions={sectorOptions}
              stageOptions={stageOptions}
              geographyOptions={geographyOptions}
            />
          ) : null
        }
      />
      <div className={styles.autoMapWrap}>
        <Section title="Or just type it in your own words">
          <AutoMapPreview examples={autoMapExamples} />
        </Section>
      </div>
    </>
  );
}
