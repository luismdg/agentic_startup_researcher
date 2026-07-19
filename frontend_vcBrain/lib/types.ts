// Shared data-model types for VC Brain mock data (/data/*.json)

export type Trend = "up" | "down" | "flat";
export type Confidence = "high" | "medium" | "low";
export type RiskAppetite = "conservative" | "balanced" | "aggressive";
export type SourcingTrack = "inbound" | "outbound";
export type OpportunityStatus =
  | "sourcing"
  | "screening"
  | "diligence"
  | "memo"
  | "decision"
  | "invested"
  | "passed";

export interface PriorVenture {
  name: string;
  role: string;
  outcome: string;
  yearStart: number;
  yearEnd: number | null;
}

export interface FounderTimelineEvent {
  date: string;
  label: string;
  detail: string;
}

export interface Founder {
  id: string;
  name: string;
  initials: string;
  location: string;
  currentStartupId: string;
  founderScore: number;
  founderScoreTrend: Trend;
  archetype: string;
  firstTimeFounder: boolean;
  bio: string;
  priorVentures: PriorVenture[];
  timeline: FounderTimelineEvent[];
}

export interface MomentumPoint {
  date: string;
  score: number;
}

export interface Startup {
  id: string;
  name: string;
  tagline: string;
  oneLiner: string;
  founderIds: string[];
  sector: string;
  stage: string;
  geography: string;
  foundedYear: number;
  website: string;
  status: OpportunityStatus;
  askAmount: number;
  proposedCheckSize: number;
  thesisFitScore: number;
  momentumTrend: Trend;
  momentumHistory: MomentumPoint[];
  lastActivityDate: string;
  tags: string[];
}

export interface AxisScore {
  score: number;
  trend: Trend;
  rationale: string;
}

export interface ScreeningHistoryPoint {
  date: string;
  founder: number;
  market: number;
  idea: number;
}

export interface Screening {
  startupId: string;
  founder: AxisScore;
  market: AxisScore;
  ideaMarketFit: AxisScore;
  history: ScreeningHistoryPoint[];
}

export interface TrustClaim {
  id: string;
  claim: string;
  source: string;
  evidenceType: string;
  confidence: Confidence;
  verifiedDate: string;
  contradiction: string | null;
}

export interface TrustScoreRecord {
  startupId: string;
  claims: TrustClaim[];
}

export type FieldAvailability = "available" | "not_disclosed" | "unavailable_at_this_stage";

export interface MemoField<T> {
  status: FieldAvailability;
  value: T | null;
}

export interface SwotContent {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface TractionKpi {
  label: string;
  value: string;
  asOf: string;
}

export interface DueDiligenceLogSummary {
  verifiedCount: number;
  openCount: number;
  contradictedCount: number;
  lastUpdated: string;
}

export interface CapTableEntry {
  holder: string;
  percent: number;
}

export interface Memo {
  startupId: string;
  generatedDate: string;
  companySnapshot: {
    name: string;
    sector: string;
    stage: string;
    geography: string;
    foundedYear: number;
    askAmount: number;
    proposedCheckSize: number;
  };
  investmentHypotheses: string[];
  swot: SwotContent;
  problemProduct: {
    problem: string;
    product: string;
  };
  tractionKpis: TractionKpi[];
  teamHistory: MemoField<string>;
  technologyDefensibility: MemoField<string>;
  marketSizing: MemoField<{ tam: string; sam: string; som: string; note: string }>;
  competition: MemoField<{ name: string; positioning: string }[]>;
  dueDiligenceLog: MemoField<DueDiligenceLogSummary>;
  financials: MemoField<{ arr: string; burnRate: string; runway: string }>;
  capTable: MemoField<CapTableEntry[]>;
  exitPerspective: MemoField<string>;
  decision: {
    recommendation: "invest" | "pass" | "watch";
    checkSize: number;
    rationale: string;
    adversarialView: {
      counterThesis: string;
      keyRisks: string[];
      whatWouldChangeOurMind: string;
    };
    portfolioFit: {
      overlapWith: string[];
      diversificationNote: string;
      concentrationRisk: Confidence;
      fitScore: number;
    };
    decidedDate: string | null;
  };
}

export type ResearchChannelType =
  | "github"
  | "hackathon"
  | "research"
  | "accelerator"
  | "community"
  | "web"
  | "network"
  | "direct";

export interface SourcingFeedItem {
  id: string;
  track: SourcingTrack;
  date: string;
  startupName: string;
  founderNames: string[];
  channel: string;
  channelType: ResearchChannelType;
  summary: string;
  status: "new" | "reviewing" | "activated" | "passed";
  activated: boolean;
  activatedDate: string | null;
  linkedStartupId: string | null;
}

export type DiligenceStatus = "verified" | "open" | "contradicted";

export interface DiligenceLogEntry {
  id: string;
  date: string;
  category: string;
  item: string;
  status: DiligenceStatus;
  notes: string;
  owner: string;
}

export interface DiligenceLog {
  startupId: string;
  entries: DiligenceLogEntry[];
}

export interface ThesisPreset {
  id: string;
  name: string;
  sectors: string[];
  stages: string[];
  geographies: string[];
  checkSizeMin: number;
  checkSizeMax: number;
  ownershipTarget: number;
  riskAppetite: RiskAppetite;
  description: string;
}

export interface ThesisAutoMapExample {
  rawInput: string;
  mappedSectors: string[];
  mappedStages: string[];
  mappedGeographies: string[];
  confidence: Confidence;
}

export interface ActiveThesis {
  activePresetId: string;
  presets: ThesisPreset[];
  autoMapExamples: ThesisAutoMapExample[];
}

export interface SourcingChannel {
  id: string;
  name: string;
  type: "accelerator" | "hackathon" | "github" | "research" | "community" | "web";
  region: string;
  activeDeals: number;
  totalSourced: number;
  conversionRate: number;
  qualityScore: number;
  lastSignalDate: string;
  notes: string;
}
