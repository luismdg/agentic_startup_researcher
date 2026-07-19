"use client";

import { useState } from "react";
import { parseCompoundQuery, isEmptyParsedQuery, type ParsedQuery } from "@/lib/queryParser";
import { RESEARCH_CHANNEL_OPTIONS } from "@/lib/data";
import Button from "@/components/ui/Button/Button";
import Badge from "@/components/ui/Badge/Badge";
import Icon from "@/components/ui/Icon/Icon";
import styles from "./QueryDetectPanel.module.css";

interface QueryDetectPanelProps {
  keyword: string;
  onDetected: (parsed: ParsedQuery) => void;
  label?: string;
}

/**
 * Reads one free-text sentence and pulls out every filter it can recognize
 * at once (industry, stage, geography, sourcing channel, founder trait) —
 * instead of making the investor click through each filter by hand.
 */
export default function QueryDetectPanel({
  keyword,
  onDetected,
  label = "Understand my search",
}: QueryDetectPanelProps) {
  const [lastParsed, setLastParsed] = useState<ParsedQuery | null>(null);

  function handleClick() {
    const parsed = parseCompoundQuery(keyword);
    setLastParsed(parsed);
    onDetected(parsed);
  }

  const geographies = lastParsed
    ? Array.from(
        new Set([...lastParsed.matchedRegions, ...lastParsed.matchedCountries, ...lastParsed.matchedCities])
      )
    : [];
  const channelLabels = lastParsed
    ? lastParsed.channelTypes.map((c) => RESEARCH_CHANNEL_OPTIONS.find((o) => o.value === c)?.label ?? c)
    : [];

  return (
    <div className={styles.wrap}>
      <Button type="button" variant="secondary" onClick={handleClick} disabled={!keyword.trim()}>
        <Icon name="link" size={14} /> {label}
      </Button>
      {lastParsed &&
        (isEmptyParsedQuery(lastParsed) ? (
          <span className={styles.empty}>
            Didn&rsquo;t catch anything specific in that — try mentioning an industry, a stage, a
            place, or how you&rsquo;d want it sourced (e.g. &ldquo;accelerator&rdquo;).
          </span>
        ) : (
          <span className={styles.detected}>
            <span className={styles.detectedLabel}>Picked up on:</span>
            {lastParsed.sectors.map((s) => (
              <Badge key={`sector-${s}`} variant="accent">
                {s}
              </Badge>
            ))}
            {lastParsed.stages.map((s) => (
              <Badge key={`stage-${s}`} variant="info">
                {s}
              </Badge>
            ))}
            {geographies.map((g) => (
              <Badge key={`geo-${g}`} variant="neutral">
                {g}
              </Badge>
            ))}
            {channelLabels.map((c) => (
              <Badge key={`channel-${c}`} variant="warning">
                {c}
              </Badge>
            ))}
            {lastParsed.founderKeywords.map((k) => (
              <Badge key={`trait-${k}`} variant="success">
                {k}
              </Badge>
            ))}
          </span>
        ))}
    </div>
  );
}
