"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { Founder, ResearchChannelType } from "@/lib/types";
import type { ParsedQuery } from "@/lib/queryParser";
import { RESEARCH_CHANNEL_OPTIONS, startupMatchesChannelTypes } from "@/lib/data";
import { SplitPanel } from "@/components/layout/SectionLayout/SectionLayout";
import GuidedFilterGate from "@/components/layout/GuidedFilterGate/GuidedFilterGate";
import { FilterGroup } from "@/components/layout/FilterPanel/FilterPanel";
import QueryDetectPanel from "@/components/layout/QueryDetectPanel/QueryDetectPanel";
import ToggleChipGroup from "@/components/ui/ToggleChipGroup/ToggleChipGroup";
import Input from "@/components/ui/Input/Input";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import FounderList from "./FounderList";
import FounderScoreCard from "./FounderScoreCard";
import styles from "./FoundersView.module.css";

type FounderHistory = "first-time" | "repeat";

const HISTORY_OPTIONS: { value: FounderHistory; label: string }[] = [
  { value: "first-time", label: "First-time founders" },
  { value: "repeat", label: "Done this before" },
];

function countryOf(location: string): string {
  const parts = location.split(",");
  return parts[parts.length - 1].trim();
}

interface FoundersViewProps {
  founders: Founder[];
  selectedId?: string;
}

export default function FoundersView({ founders, selectedId }: FoundersViewProps) {
  const router = useRouter();
  const [applied, setApplied] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [archetypes, setArchetypes] = useState<string[]>([]);
  const [history, setHistory] = useState<FounderHistory[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [minScore, setMinScore] = useState("");
  const [channelTypes, setChannelTypes] = useState<ResearchChannelType[]>([]);

  const archetypeOptions = useMemo(
    () =>
      Array.from(new Set(founders.map((f) => f.archetype)))
        .sort()
        .map((a) => ({ value: a, label: a })),
    [founders]
  );
  const countryOptions = useMemo(
    () =>
      Array.from(new Set(founders.map((f) => countryOf(f.location))))
        .sort()
        .map((c) => ({ value: c, label: c })),
    [founders]
  );

  function handleDetected(parsed: ParsedQuery) {
    if (parsed.matchedCountries.length > 0) {
      setCountries((prev) => Array.from(new Set([...prev, ...parsed.matchedCountries])));
    }
    if (parsed.channelTypes.length > 0) {
      setChannelTypes((prev) => Array.from(new Set([...prev, ...parsed.channelTypes])));
    }
    if (parsed.founderKeywords.length > 0) {
      const matchedArchetypes = archetypeOptions
        .map((o) => o.value)
        .filter((a) => parsed.founderKeywords.some((k) => a.toLowerCase().includes(k)));
      if (matchedArchetypes.length > 0) {
        setArchetypes((prev) => Array.from(new Set([...prev, ...matchedArchetypes])));
      }
      const newHistory: FounderHistory[] = [];
      if (parsed.founderKeywords.some((k) => k.includes("first"))) newHistory.push("first-time");
      if (parsed.founderKeywords.some((k) => k === "repeat" || k === "serial")) newHistory.push("repeat");
      if (newHistory.length > 0) {
        setHistory((prev) => Array.from(new Set([...prev, ...newHistory])));
      }
    }
  }

  const filtered = useMemo(() => {
    const min = minScore ? Number(minScore) : null;
    const q = keyword.trim().toLowerCase();
    return founders
      .filter((f) => {
        if (archetypes.length > 0 && !archetypes.includes(f.archetype)) return false;
        if (history.length > 0) {
          const bucket: FounderHistory = f.firstTimeFounder ? "first-time" : "repeat";
          if (!history.includes(bucket)) return false;
        }
        if (countries.length > 0 && !countries.includes(countryOf(f.location))) return false;
        if (min !== null && f.founderScore < min) return false;
        if (!startupMatchesChannelTypes(f.currentStartupId, channelTypes)) return false;
        if (q) {
          const haystack = [f.name, f.bio, f.archetype, f.location].join(" ").toLowerCase();
          if (!haystack.includes(q)) return false;
        }
        return true;
      })
      .sort((a, b) => b.founderScore - a.founderScore);
  }, [founders, archetypes, history, countries, minScore, channelTypes, keyword]);

  const summary =
    !keyword &&
    archetypes.length === 0 &&
    history.length === 0 &&
    countries.length === 0 &&
    !minScore &&
    channelTypes.length === 0 ? (
      <span>Showing everyone &middot; {filtered.length} results</span>
    ) : (
      <>
        {keyword && <span>&ldquo;{keyword}&rdquo;</span>}
        {archetypes.length > 0 && <span>{archetypes.join(", ")}</span>}
        {history.length > 0 && (
          <span>
            {history
              .map((h) => HISTORY_OPTIONS.find((o) => o.value === h)?.label ?? h)
              .join(", ")}
          </span>
        )}
        {countries.length > 0 && <span>{countries.join(", ")}</span>}
        {minScore && <span>Score {minScore}+</span>}
        {channelTypes.length > 0 && <span>{channelTypes.length} source(s)</span>}
        <span>{filtered.length} results</span>
      </>
    );

  const selected = (selectedId && filtered.find((f) => f.id === selectedId)) || filtered[0];

  return (
    <>
      <GuidedFilterGate
        icon="founders"
        eyebrow="Let's find the right people"
        title="What kind of founders do you want to see?"
        description="Type a name or keyword, or pick from the options below — then hit the button. Nothing shows until you do."
        applied={applied}
        onApply={() => setApplied(true)}
        actionLabel="Show founders"
        summary={summary}
        keyword={keyword}
        onKeywordChange={setKeyword}
        keywordPlaceholder="Try a name, background, or place…"
      >
        {keyword.trim() && (
          <FilterGroup label="One sentence, several filters at once">
            <QueryDetectPanel keyword={keyword} onDetected={handleDetected} />
          </FilterGroup>
        )}
        <FilterGroup label="What kind of founder?">
          <ToggleChipGroup
            options={archetypeOptions}
            selected={archetypes}
            onChange={setArchetypes}
            aria-label="Filter by founder type"
          />
        </FilterGroup>
        <FilterGroup label="First time, or done this before?">
          <ToggleChipGroup
            options={HISTORY_OPTIONS}
            selected={history}
            onChange={(values) => setHistory(values as FounderHistory[])}
            aria-label="Filter by founder history"
          />
        </FilterGroup>
        <FilterGroup label="Where">
          <ToggleChipGroup
            options={countryOptions}
            selected={countries}
            onChange={setCountries}
            aria-label="Filter by location"
          />
        </FilterGroup>
        <FilterGroup label="How good, at minimum? (0–100)">
          <Input
            className={styles.scoreInput}
            type="number"
            inputMode="numeric"
            min={0}
            max={100}
            placeholder="0"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
            aria-label="Minimum founder score"
          />
        </FilterGroup>
        <FilterGroup label="Where should we look?">
          <ToggleChipGroup
            options={RESEARCH_CHANNEL_OPTIONS}
            selected={channelTypes}
            onChange={(values) => setChannelTypes(values as ResearchChannelType[])}
            aria-label="Filter by discovery source"
          />
        </FilterGroup>
      </GuidedFilterGate>
      {!applied ? (
        <EmptyState
          icon="founders"
          title="Tell us who you're looking for above"
          description="Nothing shows until you search — that way you only see the people who match."
        />
      ) : filtered.length === 0 || !selected ? (
        <EmptyState
          icon="confused"
          title="No one matches that"
          description="Try loosening your search above and look again."
        />
      ) : (
        <SplitPanel
          list={
            <FounderList
              founders={filtered}
              selectedId={selected.id}
              onSelect={(id) => router.push(`/founders?founder=${id}`)}
            />
          }
          detail={<FounderScoreCard founder={selected} />}
        />
      )}
    </>
  );
}
