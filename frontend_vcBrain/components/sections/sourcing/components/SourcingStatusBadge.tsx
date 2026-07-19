import Badge, { type BadgeVariant } from "@/components/ui/Badge/Badge";
import type { SourcingFeedItem } from "@/lib/types";

type FeedStatus = SourcingFeedItem["status"];

const VARIANT: Record<FeedStatus, BadgeVariant> = {
  new: "info",
  reviewing: "neutral",
  activated: "success",
  passed: "danger",
};

const LABEL: Record<FeedStatus, string> = {
  new: "New",
  reviewing: "Reviewing",
  activated: "Activated",
  passed: "Passed",
};

export default function SourcingStatusBadge({ status }: { status: FeedStatus }) {
  return <Badge variant={VARIANT[status]}>{LABEL[status]}</Badge>;
}
