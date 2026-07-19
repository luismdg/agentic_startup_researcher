"use client";

import { useMemo, useState } from "react";
import type { Confidence, ThesisAutoMapExample } from "@/lib/types";
import { parseCompoundQuery, isEmptyParsedQuery } from "@/lib/queryParser";
import { RESEARCH_CHANNEL_OPTIONS } from "@/lib/data";
import Input from "@/components/ui/Input/Input";
import Badge from "@/components/ui/Badge/Badge";
import ConfidenceMeter from "@/components/ui/ConfidenceMeter/ConfidenceMeter";
import styles from "./AutoMapPreview.module.css";

function confidenceFor(hitCategories: number): Confidence {
  return hitCategories >= 3 ? "high" : hitCategories >= 1 ? "medium" : "low";
}

export default function AutoMapPreview({ examples }: { examples: ThesisAutoMapExample[] }) {
  const [text, setText] = useState("");

  const parsed = useMemo(() => (text.trim() ? parseCompoundQuery(text) : null), [text]);
  const nothingFound = parsed ? isEmptyParsedQuery(parsed) : false;

  const geographies = parsed
    ? Array.from(new Set([...parsed.matchedRegions, ...parsed.matchedCountries, ...parsed.matchedCities]))
    : [];
  const channelLabels = parsed
    ? parsed.channelTypes.map(
        (c) => RESEARCH_CHANNEL_OPTIONS.find((o) => o.value === c)?.label ?? c
      )
    : [];

  const hitCategories = parsed
    ? [
        parsed.sectors.length > 0,
        parsed.stages.length > 0,
        geographies.length > 0,
        parsed.channelTypes.length > 0,
        parsed.founderKeywords.length > 0,
      ].filter(Boolean).length
    : 0;

  return (
    <div className={styles.wrap}>
      <p className={styles.hint}>
        Don&rsquo;t want to click through checkboxes? Type a whole sentence, in your own words —
        stack as many details as you want in one go, like &ldquo;technical founder, Berlin, AI
        infra, top-tier accelerator&rdquo; — and we&rsquo;ll pull out every filter we can recognize
        at once, not one at a time.
      </p>
      <Input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type what you're looking for…"
        aria-label="Describe what you're looking for"
      />
      <div className={styles.suggestions}>
        {examples.map((ex) => (
          <button
            key={ex.rawInput}
            type="button"
            className={styles.suggestionChip}
            onClick={() => setText(ex.rawInput)}
          >
            &ldquo;{ex.rawInput}&rdquo;
          </button>
        ))}
      </div>

      {parsed && (
        <div className={styles.result}>
          {nothingFound ? (
            <p className={styles.notSure}>
              We couldn&rsquo;t quite figure that out. Try mentioning an industry (like
              &ldquo;fintech&rdquo; or &ldquo;AI&rdquo;), a stage (like &ldquo;seed&rdquo;), a place
              (like &ldquo;Europe&rdquo; or a city), or how you&rsquo;d want it sourced (like
              &ldquo;accelerator&rdquo; or &ldquo;GitHub&rdquo;).
            </p>
          ) : (
            <div className={styles.mapGrid}>
              <div className={styles.mapGroup}>
                <span className={styles.mapLabel}>Industries</span>
                <div className={styles.chips}>
                  {parsed.sectors.length === 0 ? (
                    <span className={styles.none}>Didn&rsquo;t catch one</span>
                  ) : (
                    parsed.sectors.map((s) => (
                      <Badge key={s} variant="accent">
                        {s}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
              <div className={styles.mapGroup}>
                <span className={styles.mapLabel}>Stage</span>
                <div className={styles.chips}>
                  {parsed.stages.length === 0 ? (
                    <span className={styles.none}>Didn&rsquo;t catch one</span>
                  ) : (
                    parsed.stages.map((s) => (
                      <Badge key={s} variant="info">
                        {s}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
              <div className={styles.mapGroup}>
                <span className={styles.mapLabel}>Where</span>
                <div className={styles.chips}>
                  {geographies.length === 0 ? (
                    <span className={styles.none}>Didn&rsquo;t catch one</span>
                  ) : (
                    geographies.map((s) => (
                      <Badge key={s} variant="neutral">
                        {s}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
              <div className={styles.mapGroup}>
                <span className={styles.mapLabel}>How to source it</span>
                <div className={styles.chips}>
                  {channelLabels.length === 0 ? (
                    <span className={styles.none}>Didn&rsquo;t catch one</span>
                  ) : (
                    channelLabels.map((s) => (
                      <Badge key={s} variant="warning">
                        {s}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
              <div className={styles.mapGroup}>
                <span className={styles.mapLabel}>Founder traits</span>
                <div className={styles.chips}>
                  {parsed.founderKeywords.length === 0 ? (
                    <span className={styles.none}>Didn&rsquo;t catch one</span>
                  ) : (
                    parsed.founderKeywords.map((s) => (
                      <Badge key={s} variant="success">
                        {s}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
              <div className={styles.mapGroup}>
                <span className={styles.mapLabel}>How sure are we?</span>
                <ConfidenceMeter level={confidenceFor(hitCategories)} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
