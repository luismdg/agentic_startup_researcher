"use client";

import { useMemo, useState } from "react";
import type { ResearchChannelType, SourcingChannel, SourcingFeedItem, SourcingTrack } from "@/lib/types";
import type { ParsedQuery } from "@/lib/queryParser";
import { RESEARCH_CHANNEL_OPTIONS } from "@/lib/data";
import { Section } from "@/components/layout/SectionLayout/SectionLayout";
import GuidedFilterGate from "@/components/layout/GuidedFilterGate/GuidedFilterGate";
import { FilterGroup } from "@/components/layout/FilterPanel/FilterPanel";
import QueryDetectPanel from "@/components/layout/QueryDetectPanel/QueryDetectPanel";
import ToggleChipGroup from "@/components/ui/ToggleChipGroup/ToggleChipGroup";
import EmptyState from "@/components/layout/EmptyState/EmptyState";
import SourcingFeedList from "./SourcingFeedList";
import ChannelTable from "./ChannelTable";
import styles from "./SourcingView.module.css";

type FeedStatus = SourcingFeedItem["status"];

const TRACK_OPTIONS: { value: SourcingTrack; label: string }[] = [
  { value: "inbound", label: "They applied to us" },
  { value: "outbound", label: "We found them" },
];

const STATUS_OPTIONS: { value: FeedStatus; label: string }[] = [
  { value: "new", label: "Just found" },
  { value: "reviewing", label: "Looking into it" },
  { value: "activated", label: "Became an application" },
  { value: "passed", label: "Passed on" },
];

interface SourcingViewProps {
  feed: SourcingFeedItem[];
  channels: SourcingChannel[];
}

export default function SourcingView({ feed, channels }: SourcingViewProps) {
  const [applied, setApplied] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [tracks, setTracks] = useState<SourcingTrack[]>([]);
  const [statuses, setStatuses] = useState<FeedStatus[]>([]);
  const [channelTypes, setChannelTypes] = useState<ResearchChannelType[]>([]);

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    return feed.filter((item) => {
      if (tracks.length > 0 && !tracks.includes(item.track)) return false;
      if (statuses.length > 0 && !statuses.includes(item.status)) return false;
      if (channelTypes.length > 0 && !channelTypes.includes(item.channelType)) return false;
      if (q) {
        const haystack = [item.startupName, item.summary, item.channel, ...item.founderNames]
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [feed, tracks, statuses, channelTypes, keyword]);

  const filteredChannels = useMemo(
    () =>
      channelTypes.length === 0
        ? channels
        : channels.filter((c) => channelTypes.includes(c.type)),
    [channels, channelTypes]
  );

  function handleDetected(parsed: ParsedQuery) {
    if (parsed.channelTypes.length > 0) {
      setChannelTypes((prev) => Array.from(new Set([...prev, ...parsed.channelTypes])));
    }
  }

  const inboundCount = feed.filter((item) => item.track === "inbound").length;
  const outboundCount = feed.filter((item) => item.track === "outbound").length;

  const summary =
    !keyword && tracks.length === 0 && statuses.length === 0 && channelTypes.length === 0 ? (
      <span>Showing everything &middot; {filtered.length} results</span>
    ) : (
      <>
        {keyword && <span>&ldquo;{keyword}&rdquo;</span>}
        {tracks.length > 0 && <span>{tracks.join(", ")}</span>}
        {statuses.length > 0 && <span>{statuses.join(", ")}</span>}
        {channelTypes.length > 0 && <span>{channelTypes.length} source(s)</span>}
        <span>{filtered.length} results</span>
      </>
    );

  return (
    <>
      <GuidedFilterGate
        icon="discover"
        eyebrow="Let's go find some startups"
        title="What kind of new startups do you want to find?"
        description="Type a keyword, or pick where to look — then run it to see what turns up. Nothing shows until you do."
        applied={applied}
        onApply={() => setApplied(true)}
        actionLabel="Find startups"
        summary={summary}
        keyword={keyword}
        onKeywordChange={setKeyword}
        keywordPlaceholder="Try a company name, technology, or founder…"
      >
        {keyword.trim() && (
          <FilterGroup label="One sentence, several filters at once">
            <QueryDetectPanel keyword={keyword} onDetected={handleDetected} />
          </FilterGroup>
        )}
        <FilterGroup label="How did we hear about them?">
          <ToggleChipGroup
            options={TRACK_OPTIONS}
            selected={tracks}
            onChange={(values) => setTracks(values as SourcingTrack[])}
            aria-label="Filter by how we found them"
          />
        </FilterGroup>
        <FilterGroup label="Where things stand">
          <ToggleChipGroup
            options={STATUS_OPTIONS}
            selected={statuses}
            onChange={(values) => setStatuses(values as FeedStatus[])}
            aria-label="Filter by status"
          />
        </FilterGroup>
        <FilterGroup label="Where should we look?">
          <ToggleChipGroup
            options={RESEARCH_CHANNEL_OPTIONS}
            selected={channelTypes}
            onChange={(values) => setChannelTypes(values as ResearchChannelType[])}
            aria-label="Filter by research channel"
          />
        </FilterGroup>
      </GuidedFilterGate>
      {!applied ? (
        <EmptyState
          icon="discover"
          title="Tell us what to look for above"
          description="Nothing shows until you search — pick where to look, or just type a keyword."
        />
      ) : (
        <>
          <p className={styles.meta}>
            {filtered.length} of {feed.length} found &middot; {inboundCount} applied directly &middot; {outboundCount} we found ourselves
          </p>
          <Section title="What we've found">
            <SourcingFeedList items={filtered} />
          </Section>
          <Section title="Where we look">
            <ChannelTable channels={filteredChannels} />
          </Section>
        </>
      )}
    </>
  );
}
