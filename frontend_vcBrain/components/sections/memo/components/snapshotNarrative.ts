import type { Memo } from "@/lib/types";

type MarketSizing = { tam: string; sam: string; som: string; note: string };

/**
 * Composes the one-paragraph "in a nutshell" snapshot: the structural
 * problem, how the product solves it, and — only when we actually have
 * the data — how big the opportunity is. Never invents a number that
 * isn't already present in the memo.
 */
export function buildSnapshotNarrative(memo: Memo, marketSizing: MarketSizing | null): string {
  const { problem, product } = memo.problemProduct;
  const marketClause = marketSizing
    ? ` The opportunity is sized at ${marketSizing.tam}, with roughly ${marketSizing.som} realistically capturable in the near term — which is why the timing matters now rather than later.`
    : "";
  return `${problem} ${memo.companySnapshot.name} addresses this directly: ${product}${marketClause}`;
}
