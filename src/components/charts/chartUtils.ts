/**
 * Shared utilities for chart components.
 * All hex values from LAILARA_DESIGN_SYSTEM.md v2 / lailara-frame.css.
 * D3 can't read CSS vars — hardcoded hex arrays are the accepted pattern.
 */

/* ── Categorical paired palette (5 families × dark + light) ──────────── */
/* Each pair: [dark at step 20, light at step 70]. 10 distinguishable     */
/* data colors with a consistent visual gap across every pair.            */

export const PAIRED_PALETTE = {
  chicago: { dark: '#1f2e7a', light: '#8e9ad0' },
  hk:      { dark: '#0c6552', light: '#6dcdb5' },
  tokyo:   { dark: '#7e1f34', light: '#e68a9a' },
  sg:      { dark: '#7a3d10', light: '#f6b97c' },
  red:     { dark: '#8e0b07', light: '#ee8880' },
} as const;

export const CATEGORICAL_COLORS: string[] = [
  '#1f2e7a', '#8e9ad0',  // Chicago
  '#0c6552', '#6dcdb5',  // Hong Kong
  '#7e1f34', '#e68a9a',  // Tokyo
  '#7a3d10', '#f6b97c',  // Singapore
  '#8e0b07', '#ee8880',  // Red
];

/* ── Sequential Hong Kong ramp (for graded/ranked series) ────────────── */

export const HK_SEQUENTIAL: string[] = [
  '#063d32', // HK-5  (darkest = largest)
  '#0a5c4b', // HK-15
  '#0e6e5a', // HK-25
  '#158f75', // HK-35
  '#1fa282', // HK-45
  '#35b595', // HK-55
  '#6dcdb5', // HK-70
  '#b5e4d8', // HK-85 (lightest = smallest)
];

/** @deprecated Use HK_SEQUENTIAL instead */
export const TEAL_PALETTE = HK_SEQUENTIAL;

/* ── Divergent palette (positive / neutral / negative) ───────────────── */

export const DIVERGENT = {
  positive: '#158f75', // HK-35
  neutral:  '#d9d9d9', // London-85
  negative: '#b82d4a', // Tokyo-40
} as const;

/* ── Semantic chart colors ───────────────────────────────────────────── */

export const CHART_COLORS = {
  gridline:  '#d9d9d9', // London-85
  reference: '#666666', // London-40 — dashed 2px
  axisText:  '#595959', // London-35
  ink:       '#0d0d0d', // London-5 — chart titles
  disabled:  '#b3b3b3', // London-70
  canvas:    '#f5f3ee', // warm off-white
  red:       '#cc100a', // Red-42 — text and 1px rules only
} as const;

/* ── Waterfall-specific colors ───────────────────────────────────────── */

export const WATERFALL_COLORS = {
  revenue:    '#1f2e7a', // Chicago-20 — starting bar
  cost:       '#b82d4a', // Tokyo-40 — subtraction steps
  net:        '#158f75', // HK-35 — final net bar
  connector:  '#d9d9d9', // London-85 — connector lines
} as const;

/* ── Segment accent colors ───────────────────────────────────────────── */

export const SEGMENT_COLORS = {
  retailer:    '#1f2e7a', // Chicago-20
  distributor: '#158f75', // HK-35
  dtc:         '#ee8a2a', // Singapore-55
} as const;

/* ── Typography tokens (for D3 attrs where CSS vars can't reach) ─────── */

export const FONTS = {
  serif: "'Playfair Display', Georgia, 'Times New Roman', serif",
  sans:  "'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif",
} as const;

/* ── Utility functions ───────────────────────────────────────────────── */

export function getSequentialColor(rank: number, total: number): string {
  if (total <= 0) return HK_SEQUENTIAL[0];

  if (total >= HK_SEQUENTIAL.length) {
    return HK_SEQUENTIAL[Math.min(rank, HK_SEQUENTIAL.length - 1)];
  }

  const step = (HK_SEQUENTIAL.length - 1) / (total - 1 || 1);
  const index = Math.round(rank * step);
  return HK_SEQUENTIAL[Math.min(index, HK_SEQUENTIAL.length - 1)];
}

/** @deprecated Use getSequentialColor instead */
export const getTealColor = getSequentialColor;

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
    formatted = millions % 1 === 0
      ? `$${millions}M`
      : `$${parseFloat(millions.toFixed(1))}M`;
  } else if (absValue >= 1_000) {
    const thousands = absValue / 1_000;
    formatted = thousands % 1 === 0
      ? `$${thousands}K`
      : `$${parseFloat(thousands.toFixed(1))}K`;
  } else {
    formatted = `$${Math.round(absValue)}`;
  }

  return isNegative ? `-${formatted}` : formatted;
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}
