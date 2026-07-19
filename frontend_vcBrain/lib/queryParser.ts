// Compound multi-attribute query parsing — resolves one free-text sentence
// into several structured filters at once (industry + stage + geography +
// sourcing channel + founder trait), rather than requiring the investor to
// click through each filter by hand. Used by the "type it in your own
// words" tool on My Focus, and by the "Understand my search" action on
// Overview, Discover, and Founders.

import { startups, founders } from "./data";
import type { ResearchChannelType } from "./types";

const SECTOR_KEYWORDS: { match: string[]; sector: string }[] = [
  { match: ["ai infra", "ai infrastructure", "gpu", "kernel", "artificial intelligence"], sector: "AI Infrastructure" },
  { match: ["climate", "carbon", "sustainability"], sector: "Climate" },
  { match: ["biotech", "drug discovery", "protein"], sector: "Biotech / AI Drug Discovery" },
  { match: ["healthcare", "health ai", "medical", "radiology"], sector: "Healthcare AI" },
  { match: ["fintech infra", "payments", "banking", "settlement"], sector: "Fintech Infrastructure" },
  { match: ["security", "cyber", "cybersecurity"], sector: "Cybersecurity" },
  { match: ["robot", "robotics", "drone"], sector: "Robotics" },
  { match: ["gaming", "netcode"], sector: "Gaming / Developer Tools" },
  { match: ["devtools", "developer tools", "database"], sector: "Developer Tools" },
  { match: ["legal tech", "legal", "contract review"], sector: "Legal Tech" },
  { match: ["agtech", "agri", "farm", "soil", "irrigation"], sector: "Agtech" },
  { match: ["space", "satellite", "orbit"], sector: "Space" },
  { match: ["hardware", "battery", "mobility", "e-bike"], sector: "Hardware / Mobility" },
  { match: ["logistics", "port", "shipping", "freight"], sector: "Logistics" },
  { match: ["edtech", "education", "tutor"], sector: "Edtech" },
  { match: ["proptech", "real estate", "lending", "mortgage"], sector: "Proptech / Fintech" },
  { match: ["marketplace"], sector: "Marketplace / Agtech" },
  { match: ["consumer social", "social app"], sector: "Consumer Social" },
];

const STAGE_KEYWORDS: { match: string[]; stage: string }[] = [
  { match: ["pre-seed", "preseed", "very early"], stage: "Pre-seed" },
  { match: ["seed"], stage: "Seed" },
  { match: ["series a"], stage: "Series A" },
];

const REGION_KEYWORDS: { match: string[]; geography: string }[] = [
  { match: ["north america", "united states", "usa"], geography: "North America" },
  { match: ["europe"], geography: "Europe" },
  { match: ["africa"], geography: "Africa" },
  { match: ["latin america", "latam"], geography: "Latin America" },
  { match: ["south asia"], geography: "South Asia" },
  { match: ["global", "anywhere", "worldwide"], geography: "Global" },
];

const CHANNEL_KEYWORDS: { match: string[]; channel: ResearchChannelType }[] = [
  { match: ["github", "open source", "open-source", "repo", "maintainer"], channel: "github" },
  { match: ["google", "web search", "press mention"], channel: "web" },
  { match: ["academic", "arxiv", "preprint", "research lab"], channel: "research" },
  { match: ["accelerator", "demo day", "top-tier accelerator"], channel: "accelerator" },
  { match: ["hackathon"], channel: "hackathon" },
  { match: ["community", "conference", "summit"], channel: "community" },
  { match: ["warm intro", "referral", "co-investor"], channel: "network" },
  { match: ["cold application", "applied directly", "direct application"], channel: "direct" },
];

const FOUNDER_TRAIT_KEYWORDS = [
  "technical",
  "domain-expert",
  "domain expert",
  "first-time",
  "first time",
  "repeat",
  "serial",
  "consumer",
];

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function wordMatch(text: string, phrase: string): boolean {
  const pattern = new RegExp(`\\b${escapeRegExp(phrase.toLowerCase())}\\b`);
  return pattern.test(text);
}

function citySegment(location: string): string {
  return location.split(",")[0].trim();
}

function countrySegment(location: string): string {
  const parts = location.split(",");
  return parts[parts.length - 1].trim();
}

export interface ParsedQuery {
  sectors: string[];
  stages: string[];
  matchedCities: string[];
  matchedCountries: string[];
  matchedRegions: string[];
  channelTypes: ResearchChannelType[];
  founderKeywords: string[];
}

export function parseCompoundQuery(raw: string): ParsedQuery {
  const text = raw.toLowerCase();

  const sectors = Array.from(
    new Set(
      SECTOR_KEYWORDS.filter((k) => k.match.some((m) => wordMatch(text, m))).map((k) => k.sector)
    )
  );
  const stages = Array.from(
    new Set(STAGE_KEYWORDS.filter((k) => k.match.some((m) => wordMatch(text, m))).map((k) => k.stage))
  );
  const matchedRegions = Array.from(
    new Set(
      REGION_KEYWORDS.filter((k) => k.match.some((m) => wordMatch(text, m))).map((k) => k.geography)
    )
  );
  const channelTypes = Array.from(
    new Set(
      CHANNEL_KEYWORDS.filter((k) => k.match.some((m) => wordMatch(text, m))).map((k) => k.channel)
    )
  );

  const allCities = new Set<string>();
  const allCountries = new Set<string>();
  startups.forEach((s) => {
    allCities.add(citySegment(s.geography));
    allCountries.add(countrySegment(s.geography));
  });
  founders.forEach((f) => {
    allCities.add(citySegment(f.location));
    allCountries.add(countrySegment(f.location));
  });

  const matchedCities = Array.from(allCities).filter((c) => wordMatch(text, c));
  const matchedCountries = Array.from(allCountries).filter((c) => wordMatch(text, c));

  const founderKeywords = FOUNDER_TRAIT_KEYWORDS.filter((k) => wordMatch(text, k));

  return {
    sectors,
    stages,
    matchedCities,
    matchedCountries,
    matchedRegions,
    channelTypes,
    founderKeywords: Array.from(new Set(founderKeywords)),
  };
}

export function isEmptyParsedQuery(parsed: ParsedQuery): boolean {
  return (
    parsed.sectors.length === 0 &&
    parsed.stages.length === 0 &&
    parsed.matchedCities.length === 0 &&
    parsed.matchedCountries.length === 0 &&
    parsed.matchedRegions.length === 0 &&
    parsed.channelTypes.length === 0 &&
    parsed.founderKeywords.length === 0
  );
}
