import type { MemoField } from "@/lib/types";

/**
 * Resolves a MemoField<T> down to its value, narrowing out `null`.
 *
 * MemoField<T> is a plain interface (status + value are independently typed),
 * not a discriminated union, so TypeScript cannot narrow `field.value` just by
 * checking `field.status === "available"` at the call site. Funnelling the
 * check through this helper's return type (`T | null`) lets ordinary variable
 * narrowing (`value !== null` / truthy checks) take over cleanly wherever the
 * result is consumed.
 */
export function availableValue<T>(field: MemoField<T>): T | null {
  return field.status === "available" ? field.value : null;
}
