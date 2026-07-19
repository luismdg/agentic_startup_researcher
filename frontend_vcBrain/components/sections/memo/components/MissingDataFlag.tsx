import EmptyValue from "@/components/ui/EmptyValue/EmptyValue";
import type { FieldAvailability } from "@/lib/types";

/**
 * Local wrapper around the shared EmptyValue component, used everywhere a
 * memo field is missing/confidential. Accepts the full FieldAvailability
 * union (rather than EmptyValue's Exclude<..., "available">) purely so call
 * sites can pass a MemoField's `status` straight through without an extra
 * type-narrowing dance; the "available" case is a defensive no-op that
 * should never actually be hit when used correctly.
 */
export default function MissingDataFlag({ reason }: { reason: FieldAvailability }) {
  if (reason === "available") return null;
  return <EmptyValue reason={reason} />;
}
