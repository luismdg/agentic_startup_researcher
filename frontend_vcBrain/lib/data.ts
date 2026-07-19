import foundersJson from "@/data/founders.json";
import startupsJson from "@/data/startups.json";
import screeningJson from "@/data/screening.json";
import trustScoresJson from "@/data/trust-scores.json";
import memosJson from "@/data/memos.json";
import sourcingFeedJson from "@/data/sourcing-feed.json";
import diligenceLogJson from "@/data/diligence-log.json";
import thesisPresetsJson from "@/data/thesis-presets.json";
import sourcingChannelsJson from "@/data/sourcing-channels.json";

import type {
  Founder,
  Startup,
  Screening,
  TrustScoreRecord,
  Memo,
  SourcingFeedItem,
  DiligenceLog,
  ActiveThesis,
  SourcingChannel,
  ResearchChannelType,
} from "./types";

export const founders = foundersJson as Founder[];
export const startups = startupsJson as Startup[];
export const screenings = screeningJson as Screening[];
export const trustScores = trustScoresJson as TrustScoreRecord[];
export const memos = memosJson as Memo[];
export const sourcingFeed = sourcingFeedJson as SourcingFeedItem[];
export const diligenceLogs = diligenceLogJson as DiligenceLog[];
export const thesis = thesisPresetsJson as ActiveThesis;
export const sourcingChannels = sourcingChannelsJson as SourcingChannel[];

export function getStartup(id: string): Startup | undefined {
  return startups.find((s) => s.id === id);
}

export function getFounder(id: string): Founder | undefined {
  return founders.find((f) => f.id === id);
}

export function getFoundersForStartup(startup: Startup): Founder[] {
  return startup.founderIds
    .map((id) => getFounder(id))
    .filter((f): f is Founder => Boolean(f));
}

export function getScreening(startupId: string): Screening | undefined {
  return screenings.find((s) => s.startupId === startupId);
}

export function getTrustScore(startupId: string): TrustScoreRecord | undefined {
  return trustScores.find((t) => t.startupId === startupId);
}

export function getMemo(startupId: string): Memo | undefined {
  return memos.find((m) => m.startupId === startupId);
}

export function getDiligenceLog(startupId: string): DiligenceLog | undefined {
  return diligenceLogs.find((d) => d.startupId === startupId);
}

export function getActiveThesisPreset() {
  return thesis.presets.find((p) => p.id === thesis.activePresetId) ?? thesis.presets[0];
}

export const RESEARCH_CHANNEL_OPTIONS: { value: ResearchChannelType; label: string }[] = [
  { value: "github", label: "GitHub" },
  { value: "web", label: "Google / Web search" },
  { value: "research", label: "Academic papers" },
  { value: "accelerator", label: "Accelerators" },
  { value: "hackathon", label: "Hackathons" },
  { value: "community", label: "Community / conferences" },
  { value: "network", label: "Warm intro / network" },
  { value: "direct", label: "Direct application" },
];

export function getStartupChannelTypes(startupId: string): ResearchChannelType[] {
  const types = sourcingFeed
    .filter((item) => item.linkedStartupId === startupId)
    .map((item) => item.channelType);
  return Array.from(new Set(types));
}

export function startupMatchesChannelTypes(
  startupId: string,
  selected: ResearchChannelType[]
): boolean {
  if (selected.length === 0) return true;
  const types = getStartupChannelTypes(startupId);
  if (types.length === 0) return false;
  return types.some((t) => selected.includes(t));
}

export function formatCurrency(amount: number): string {
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(amount % 1_000_000 === 0 ? 0 : 1)}M`;
  if (amount >= 1_000) return `$${Math.round(amount / 1_000)}K`;
  return `$${amount}`;
}

export function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00Z").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
