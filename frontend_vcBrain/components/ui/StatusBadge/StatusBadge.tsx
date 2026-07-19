import Badge, { type BadgeVariant } from "@/components/ui/Badge/Badge";
import type { OpportunityStatus } from "@/lib/types";

const VARIANT: Record<OpportunityStatus, BadgeVariant> = {
  sourcing: "neutral",
  screening: "info",
  diligence: "warning",
  memo: "accent",
  decision: "accent",
  invested: "success",
  passed: "danger",
};

const LABEL: Record<OpportunityStatus, string> = {
  sourcing: "Sourcing",
  screening: "Screening",
  diligence: "Diligence",
  memo: "Memo",
  decision: "Decision",
  invested: "Invested",
  passed: "Passed",
};

export default function StatusBadge({ status }: { status: OpportunityStatus }) {
  return <Badge variant={VARIANT[status]}>{LABEL[status]}</Badge>;
}
