"use client";

import { useMemo, useState } from "react";
import type { ResearchChannelType, Screening, Startup, Trend } from "@/lib/types";
import type { ParsedQuery } from "@/lib/queryParser";
import { RESEARCH_CHANNEL_OPTIONS, startupMatchesChannelTypes } from "@/lib/data";
import GuidedFilterGate from "@/components/layout/GuidedFilterGate/GuidedFilterGate";
import { FilterGroup } from "@/components/layout/FilterPanel/FilterPanel";
import QueryDetectPanel from "@/components/layout/QueryDetectPanel/QueryDetectPanel";
import ToggleChipGroup from "@/components/ui/ToggleChipGroup/ToggleChipGroup";
import Input from "@/components/ui/Input/Input";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import PulseStrip from "./PulseStrip";
import RankedList from "./RankedList";
import styles from "./DashboardView.module.css";

const TREND_OPTIONS: { value: Trend; label: string }[] = [
  { value: "up", label: "Getting better" },
  { value: "flat", label: "Staying steady" },
  { value: "down", label: "Getting worse" },
];

function countryOf(geography: string): string {
  const parts = geography.split(",");
  return parts[parts.length - 1].trim();
}

interface DashboardViewProps {
  startups: Startup[];
  liveScreenings?: Record<string, Screening>;
}

export default function DashboardView({ startups, liveScreenings = {} }: DashboardViewProps) {
  const [applied, setApplied] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);
  const [stages, setStages] = useState<string[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [channelTypes, setChannelTypes] = useState<ResearchChannelType[]>([]);
  const [askMin, setAskMin] = useState("");
  const [askMax, setAskMax] = useState("");

  const sectorOptions = useMemo(
    () =>
      Array.from(new Set(startups.map((s) => s.sector)))
        .sort()
        .map((s) => ({ value: s, label: s })),
    [startups]
  );
  const stageOptions = useMemo(
    () =>
      Array.from(new Set(startups.map((s) => s.stage)))
        .sort()
        .map((s) => ({ value: s, label: s })),
    [startups]
  );
  const countryOptions = useMemo(
    () =>
      Array.from(new Set(startups.map((s) => countryOf(s.geography))))
        .sort()
        .map((c) => ({ value: c, label: c })),
    [startups]
  );

  function handleDetected(parsed: ParsedQuery) {
    if (parsed.sectors.length > 0) {
      setSectors((prev) => Array.from(new Set([...prev, ...parsed.sectors])));
    }
    if (parsed.stages.length > 0) {
      setStages((prev) => Array.from(new Set([...prev, ...parsed.stages])));
    }
    if (parsed.matchedCountries.length > 0) {
      setCountries((prev) => Array.from(new Set([...prev, ...parsed.matchedCountries])));
    }
    if (parsed.channelTypes.length > 0) {
      setChannelTypes((prev) => Array.from(new Set([...prev, ...parsed.channelTypes])));
    }
  }

  const filtered = useMemo(() => {
    const min = askMin ? Number(askMin) * 1000 : null;
    const max = askMax ? Number(askMax) * 1000 : null;
    const q = keyword.trim().toLowerCase();
    return startups.filter((s) => {
      if (sectors.length > 0 && !sectors.includes(s.sector)) return false;
      if (stages.length > 0 && !stages.includes(s.stage)) return false;
      if (countries.length > 0 && !countries.includes(countryOf(s.geography))) return false;
      if (trends.length > 0 && !trends.includes(s.momentumTrend)) return false;
      if (min !== null && s.askAmount < min) return false;
      if (max !== null && s.askAmount > max) return false;
      if (!startupMatchesChannelTypes(s.id, channelTypes)) return false;
      if (q) {
        const haystack = [s.name, s.tagline, s.oneLiner, s.sector, s.stage, s.geography, ...s.tags]
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [startups, sectors, stages, countries, trends, askMin, askMax, channelTypes, keyword]);

  const summary =
    !keyword &&
    sectors.length === 0 &&
    stages.length === 0 &&
    countries.length === 0 &&
    trends.length === 0 &&
    channelTypes.length === 0 &&
    !askMin &&
    !askMax ? (
      <span>Showing everything · {filtered.length} results</span>
    ) : (
      <>
        {keyword && <span>&ldquo;{keyword}&rdquo;</span>}
        {sectors.length > 0 && <span>Industry: {sectors.join(", ")}</span>}
        {stages.length > 0 && <span>Stage: {stages.join(", ")}</span>}
        {countries.length > 0 && <span>Where: {countries.join(", ")}</span>}
        {trends.length > 0 && <span>Trend: {trends.join(", ")}</span>}
        {channelTypes.length > 0 && <span>Found via: {channelTypes.length} source(s)</span>}
        {(askMin || askMax) && (
          <span>
            Raising: ${askMin || "0"}K–{askMax || "any"}K
          </span>
        )}
        <span>{filtered.length} results</span>
      </>
    );

  return (
    <>
      <GuidedFilterGate
        icon="focus"
        eyebrow="Let's find what you want"
        title="What kind of startups do you want to see?"
        description="Type a keyword, or pick from the options below — then hit the button to see your list. Nothing shows until you do."
        applied={applied}
        onApply={() => setApplied(true)}
        actionLabel="Show me the list"
        summary={summary}
        keyword={keyword}
        onKeywordChange={setKeyword}
        keywordPlaceholder="Try a company name, industry, or idea…"
      >
        {keyword.trim() && (
          <FilterGroup label="One sentence, several filters at once">
            <QueryDetectPanel keyword={keyword} onDetected={handleDetected} />
          </FilterGroup>
        )}
        <FilterGroup label="Industry">
          <ToggleChipGroup
            options={sectorOptions}
            selected={sectors}
            onChange={setSectors}
            aria-label="Filter by industry"
          />
        </FilterGroup>
        <FilterGroup label="How early?">
          <ToggleChipGroup
            options={stageOptions}
            selected={stages}
            onChange={setStages}
            aria-label="Filter by stage"
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
        <FilterGroup label="Getting better or worse lately?">
          <ToggleChipGroup
            options={TREND_OPTIONS}
            selected={trends}
            onChange={(values) => setTrends(values as Trend[])}
            aria-label="Filter by momentum"
          />
        </FilterGroup>
        <FilterGroup label="How much they're raising ($K)">
          <div className={styles.range}>
            <Input
              type="number"
              inputMode="numeric"
              placeholder="Min"
              value={askMin}
              onChange={(e) => setAskMin(e.target.value)}
              aria-label="Minimum amount in thousands"
            />
            <span className={styles.rangeSep} aria-hidden="true">
              –
            </span>
            <Input
              type="number"
              inputMode="numeric"
              placeholder="Max"
              value={askMax}
              onChange={(e) => setAskMax(e.target.value)}
              aria-label="Maximum amount in thousands"
            />
          </div>
        </FilterGroup>
        <FilterGroup label="Where should we look for these?">
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
          icon="focus"
          title="Tell us what you're looking for above"
          description="Nothing shows until you search — that way you only ever see what you actually asked for."
        />
      ) : (
        <>
          <PulseStrip startups={filtered} />
          <RankedList startups={filtered} liveScreenings={liveScreenings} />
        </>
      )}
    </>
  );
}
