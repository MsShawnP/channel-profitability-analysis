/**
 * Shared utilities for chart components.
 * Formatting, palette lookup, and constants used across chart files.
 */

/** Hong Kong sequential teal — Lailara Design System v2. */
export const TEAL_PALETTE: string[] = [
  '#063d32', // HK-5  (darkest = largest)
  '#0a5c4b', // HK-15
  '#0e6e5a', // HK-25
  '#158f75', // HK-35
  '#1fa282', // HK-45
  '#35b595', // HK-55
  '#6dcdb5', // HK-70
  '#b5e4d8', // HK-85 (lightest = smallest)
];

/**
 * Returns the teal palette color for a given rank.
 * rank is 0-indexed: rank 0 = largest value = darkest color.
 * If rank exceeds palette length, wraps to the lightest color.
 */
export function getTealColor(rank: number, total: number): string {
  if (total <= 0) return TEAL_PALETTE[0];

  // Map rank to palette index. If fewer items than palette entries,
  // distribute evenly across the palette. If more, clamp to lightest.
  if (total >= TEAL_PALETTE.length) {
    return TEAL_PALETTE[Math.min(rank, TEAL_PALETTE.length - 1)];
  }

  // Fewer items than palette entries: space them evenly
  const step = (TEAL_PALETTE.length - 1) / (total - 1 || 1);
  const index = Math.round(rank * step);
  return TEAL_PALETTE[Math.min(index, TEAL_PALETTE.length - 1)];
}

/**
 * Formats a dollar value compactly for chart labels and axes.
 * Examples: $1.2M, $345K, $0, -$50K
 */
export const DIM_OPACITY = 0.2;

export function getOpacity(pinnedItem: string | null, currentItem: string): number {
  if (!pinnedItem) return 1;
  return currentItem === pinnedItem ? 1 : DIM_OPACITY;
}

export function formatCompact(value: number): string {
  if (value === 0) return '$0';

  const isNegative = value < 0;
  const absValue = Math.abs(value);
  let formatted: string;

  if (absValue >= 1_000_000) {
    const millions = absValue / 1_000_000;
    // Show one decimal if it matters, otherwise whole number
    formatted = millions % 1 === 0
      ? `$${millions}M`
      : `$${parseFloat(millions.toFixed(1))}M`;
  } else if (absValue >= 1_000) {
    const thousands = absValue / 1_000;
    formatted = thousands % 1 === 0
      ? `$${thousands}K`
      : `$${parseFloat(thousands.toFixed(1))}K`;
  } else {
    formatted = `$${absValue}`;
  }

  return isNegative ? `-${formatted}` : formatted;
}
