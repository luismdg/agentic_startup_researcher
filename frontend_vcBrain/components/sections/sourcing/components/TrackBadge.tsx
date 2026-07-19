import Badge, { type BadgeVariant } from "@/components/ui/Badge/Badge";
import type { SourcingTrack } from "@/lib/types";

const VARIANT: Record<SourcingTrack, BadgeVariant> = {
  inbound: "accent",
  outbound: "warning",
};

const LABEL: Record<SourcingTrack, string> = {
  inbound: "Inbound",
  outbound: "Outbound",
};

export default function TrackBadge({ track }: { track: SourcingTrack }) {
  return <Badge variant={VARIANT[track]}>{LABEL[track]}</Badge>;
}
