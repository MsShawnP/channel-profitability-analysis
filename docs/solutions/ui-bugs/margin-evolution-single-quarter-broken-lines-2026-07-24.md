---
title: D3 line chart renders broken when single quarter selected
date: 2026-07-24
category: ui-bugs
module: charts
problem_type: ui_bug
component: frontend_stimulus
severity: medium
symptoms:
  - "All data points stacked at x=0 (left edge) when single quarter selected"
  - "No connecting lines visible between data points in single-quarter view"
  - "MarginEvolutionChart appeared broken/empty under single-quarter time filter"
root_cause: logic_error
resolution_type: code_fix
tags:
  - d3
  - react
  - scalepoint
  - line-chart
  - edge-case
  - single-data-point
  - time-filter
related_components:
  - MarginEvolutionChart
  - TimeFilter
---

# D3 line chart renders broken when single quarter selected

## Problem

When a single quarter is selected in the time filter, the Margin Evolution line chart rendered broken/invisible lines. All channel data points stacked at x=0 with no visible connecting lines, making the chart appear empty.

## Symptoms

- All channel data points stacked at the left edge of the chart (x=0) when any individual quarter was selected from the quarter dropdown.
- No connecting lines visible between data points in single-quarter view.
- Right-side channel labels still appeared with correct margin percentages, but the chart body was empty.
- Multi-quarter views (full range, fiscal years) rendered correctly — the bug was specific to single-quarter selection.

## What Didn't Work

No extended investigation was needed. The problem was identified visually from a screenshot the user provided showing the broken chart with Q1 2023 selected. The root cause was immediately apparent from reading the D3 rendering code.

The bug was latent from the original chart build (session history). Two earlier decisions created the precondition: (1) the all-quarters dropdown was added to `TimeFilter.tsx`, making single-quarter selection a reachable UI state, and (2) `filteredTrends` was wired through to `MarginEvolutionChart`, so single-quarter data actually reached the chart as a 1-element array. Neither change was tested against a single-quarter selection at the time. (session history)

## Solution

Two changes in `src/components/charts/MarginEvolutionChart.tsx`:

**1. Added single-quarter detection:**

```tsx
const singleQuarter = quarters.length === 1;
```

**2. Replaced path rendering with circle rendering when `singleQuarter` is true:**

Before (unconditional path):
```tsx
g.append('path')
  .datum(series)
  .attr('fill', 'none')
  .attr('stroke', color)
  .attr('stroke-width', isolated === ch ? 2.5 : 1.5)
  .attr('stroke-opacity', opacity)
  .attr('d', lineFn)
  .style('cursor', 'pointer')
  .on('click', () => setIsolated(prev => prev === ch ? null : ch));
```

After (conditional):
```tsx
if (singleQuarter) {
  g.append('circle')
    .attr('cx', innerW / 2)
    .attr('cy', y(series[0].margin))
    .attr('r', isolated === ch ? 5 : 4)
    .attr('fill', color)
    .attr('opacity', opacity)
    .style('cursor', 'pointer')
    .on('click', () => setIsolated(prev => prev === ch ? null : ch));
} else {
  g.append('path')
    .datum(series)
    .attr('fill', 'none')
    .attr('stroke', color)
    .attr('stroke-width', isolated === ch ? 2.5 : 1.5)
    .attr('stroke-opacity', opacity)
    .attr('d', lineFn)
    .style('cursor', 'pointer')
    .on('click', () => setIsolated(prev => prev === ch ? null : ch));
}
```

Circles use radius 5 for the isolated (clicked) channel and 4 otherwise, maintaining the visual distinction that line charts use via stroke-width (2.5 vs 1.5). Click-to-isolate interaction is preserved on circles.

## Why This Works

Two D3 behaviors combine to cause the bug:

1. **`scalePoint` with a single domain value** maps that value to the start of the range (x=0), not the center. Every channel's data point gets the same x-coordinate at the left edge.

2. **`d3Line` with a single point** generates a degenerate SVG path — either an empty string or a `M x,y` with no `L` segment. SVG renders nothing visible for a path with no line segments.

The fix addresses both: it centers the x-coordinate at `innerW / 2` so the single quarter's data appears in the middle of the chart, and switches from `<path>` to `<circle>` since a dot is the correct visual representation of a single data point — there is no trend to draw a line through.

This is the same class of D3 edge case as the `clientWidth` zero-width bug found in the same codebase (session history): D3 code carrying an assumption (nonzero container width / multiple data points) that breaks on a degenerate input.

## Prevention

1. **Test edge cases for filter-driven charts.** Any chart that accepts a variable-length domain from a filter should be tested with domain sizes of 0, 1, and 2+ items. Single-element domains are the most common miss because multi-element cases work fine and mask the issue.

2. **Treat D3 scale + shape edge cases as a known pattern.** `scalePoint`/`scaleBand` with one domain value and `d3Line`/`d3Area` with one data point are documented D3 behaviors. When building any D3 chart that depends on user-controlled filtering, add a guard for the single-item case at construction time.

3. **Visual QA across all filter states.** Time-filtered charts should be checked in each filter mode (full range, single fiscal year, single quarter) before marking the chart complete. Passing data tests does not confirm visual rendering works — visual verification is required (see DECISIONS.md, "Prose-data tests validate pipeline math, not UI rendering").

## Related Issues

- **At-risk sibling:** `src/components/charts/TrendChart.tsx` uses the same `scalePoint` + `d3Line` pattern without a single-quarter guard. Its dots (`DOT_RADIUS = 3`) would still render, but line paths would likely be invisible for a single quarter.
- **Related precedent:** `clientWidth` zero-width chart bug (same session, same codebase) — D3 code assumed nonzero container width, used `?? 600` which doesn't catch `0`. Same class of degenerate-input assumption.
- **DECISIONS.md:** "Strategic recommendations use full-range data regardless of time filter" — related time-filter edge case in the same UI surface.
- **FAILURES.md:** "Action cards computed overhead from time-filtered data (returned $0)" — same trigger (single-quarter selection), different root cause (data granularity vs. rendering).
