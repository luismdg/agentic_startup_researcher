"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button/Button";
import Input from "@/components/ui/Input/Input";
import Select from "@/components/ui/Select/Select";
import ToggleChipGroup from "@/components/ui/ToggleChipGroup/ToggleChipGroup";
import Icon from "@/components/ui/Icon/Icon";
import styles from "./AgenticSearchForm.module.css";

// Mirrors src/data/filter-options.json on the sourcing backend -- these are
// validated there (Node 1), not here; this is just what the datalist/chips
// suggest. Free text is still accepted for niche/geography either way.
const NICHE_SUGGESTIONS = ["Mexican LegalTech", "LatAm B2B SaaS", "Climate Hardware", "AI Infra", "Healthtech"];
const GEOGRAPHY_SUGGESTIONS = ["Mexico", "Colombia", "Brazil", "United States", "Germany"];
const CHANNEL_OPTIONS = [
  { value: "GitHub", label: "GitHub" },
  { value: "Google", label: "Google" },
  { value: "Academic papers", label: "Academic papers" },
  { value: "Accelerators", label: "Accelerators" },
  { value: "Hackathons", label: "Hackathons" },
  { value: "Community", label: "Community (Reddit/LinkedIn)" },
  { value: "Direct application", label: "Direct application" },
  { value: "YouTube", label: "YouTube" },
  { value: "Twitter/X", label: "Twitter/X" },
  { value: "Reddit", label: "Reddit" },
];
const STAGE_OPTIONS = [
  { value: "", label: "Any stage" },
  { value: "Idea", label: "Idea" },
  { value: "MVP", label: "MVP" },
  { value: "Launched", label: "Launched" },
  { value: "Unknown", label: "Unknown" },
];

type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; resultsFound: number; ingested: number }
  | { kind: "error"; message: string };

export default function AgenticSearchForm() {
  const router = useRouter();
  const [niche, setNiche] = useState("");
  const [geography, setGeography] = useState("");
  const [keywordDraft, setKeywordDraft] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [channels, setChannels] = useState<string[]>([]);
  const [stageSignal, setStageSignal] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  function addKeyword() {
    const value = keywordDraft.trim();
    if (value && !keywords.includes(value)) {
      setKeywords([...keywords, value]);
    }
    setKeywordDraft("");
  }

  function handleKeywordKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addKeyword();
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!niche.trim() || status.kind === "loading") return;

    setStatus({ kind: "loading" });
    const controller = new AbortController();
    // Real agentic browsing across several channels can genuinely take a
    // couple of minutes -- generous on purpose, not a UI bug if it sits here.
    const timeout = setTimeout(() => controller.abort(), 150_000);

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ niche, geography, keywords, channels, stageSignal }),
        signal: controller.signal,
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        setStatus({ kind: "error", message: data.error ?? "The search failed for an unknown reason." });
        return;
      }
      setStatus({ kind: "success", resultsFound: data.resultsFound, ingested: data.ingested });
      router.refresh();
    } catch (err) {
      const aborted = err instanceof DOMException && err.name === "AbortError";
      setStatus({
        kind: "error",
        message: aborted
          ? "The search timed out after 2.5 minutes. It may still be running on the backend -- check its terminal."
          : "Couldn't reach the search API route.",
      });
    } finally {
      clearTimeout(timeout);
    }
  }

  const loading = status.kind === "loading";

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>
          <Icon name="sprout" size={14} /> Go find new startups
        </span>
        <h2 className={styles.title}>Run a real agentic search</h2>
        <p className={styles.description}>
          This actually browses the web (GitHub, Google, LinkedIn, Reddit, and more) for
          low-visibility candidates matching what you type below, then scores and files whatever
          it finds. Can take a minute or two — it&rsquo;s doing real research, not a lookup.
        </p>
      </div>

      <div className={styles.grid}>
        <label className={styles.field}>
          <span className={styles.label}>Niche</span>
          <Input
            list="niche-suggestions"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            placeholder="e.g. Mexican LegalTech"
            required
          />
          <datalist id="niche-suggestions">
            {NICHE_SUGGESTIONS.map((n) => (
              <option key={n} value={n} />
            ))}
          </datalist>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Country / geography</span>
          <Input
            list="geography-suggestions"
            value={geography}
            onChange={(e) => setGeography(e.target.value)}
            placeholder="e.g. Mexico"
          />
          <datalist id="geography-suggestions">
            {GEOGRAPHY_SUGGESTIONS.map((g) => (
              <option key={g} value={g} />
            ))}
          </datalist>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Stage</span>
          <Select value={stageSignal} onChange={setStageSignal} options={STAGE_OPTIONS} aria-label="Stage signal" />
        </label>
      </div>

      <div className={styles.field}>
        <span className={styles.label}>Keywords</span>
        <div className={styles.keywordRow}>
          <Input
            value={keywordDraft}
            onChange={(e) => setKeywordDraft(e.target.value)}
            onKeyDown={handleKeywordKeyDown}
            onBlur={addKeyword}
            placeholder="Type a phrase, press Enter…"
            className={styles.keywordInput}
          />
        </div>
        {keywords.length > 0 && (
          <div className={styles.chips}>
            {keywords.map((k) => (
              <button
                key={k}
                type="button"
                className={styles.chip}
                onClick={() => setKeywords(keywords.filter((v) => v !== k))}
                aria-label={`Remove keyword ${k}`}
              >
                {k} <span aria-hidden="true">×</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className={styles.field}>
        <span className={styles.label}>Where to look (optional — leave blank to use the niche&rsquo;s defaults)</span>
        <ToggleChipGroup options={CHANNEL_OPTIONS} selected={channels} onChange={setChannels} aria-label="Channels" />
      </div>

      <div className={styles.actions}>
        <Button type="submit" variant="primary" disabled={!niche.trim() || loading}>
          {loading ? "Searching…" : "Search the web"}
        </Button>
        {status.kind === "success" && (
          <span className={styles.success}>
            <Icon name="check" size={14} /> Found {status.resultsFound} candidate
            {status.resultsFound === 1 ? "" : "s"}, added {status.ingested} to the feed below.
          </span>
        )}
        {status.kind === "error" && <span className={styles.error}>{status.message}</span>}
      </div>
    </form>
  );
}
