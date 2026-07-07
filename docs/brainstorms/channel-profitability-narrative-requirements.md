---
date: 2026-05-16
topic: channel-profitability-narrative
---

# Channel Profitability Narrative

## Summary

A scrollable, Economist-style web narrative that progressively reveals
how Cinderhaven's channel profitability picture transforms as cost
layers are stacked on revenue — opening with a provocative headline
number and closing with a capital allocation reframe. Built with Astro,
React/D3 chart islands, and static JSON from the Cinderhaven Data
Platform.

---

## Problem Frame

Cinderhaven generates ~$25M in annual revenue across six channels.
Walmart alone accounts for 50% of top-line revenue. The executive
mental model is shaped by this revenue picture — and it looks healthy.

But revenue is not contribution. Channel-specific costs — deductions,
OTIF fines, labeling penalties, compliance overhead, triage labor —
erode margin unevenly across channels. The sibling Trade Spend
Diagnostic established a 4-point margin gap ($1M/year in operational
waste), but that project answers "how much is leaking." It does not
answer "given the true contribution by channel, where should capital
go instead."

Lean CPG operators rarely build the accounting infrastructure to see
contribution by channel. They see the revenue and assume the biggest
channel is the best channel. This analysis exists to prove — with
layered evidence an executive can verify — that revenue share and
contribution share tell very different stories.

---

## Actors

- A1. Portfolio viewer: evaluates the creator's analytical and
  communication skills by experiencing the finished deliverable
- A2. Fictional executive (implicit audience): the persona the
  narrative is tuned for — a CPG decision-maker who knows their
  revenue by channel but hasn't seen contribution broken out

---

## Key Flows

- F1. Primary reading flow
  - **Trigger:** Viewer lands on the page
  - **Actors:** A1, A2
  - **Steps:**
    1. Read provocative headline claim (number-driven)
    2. Orient to Cinderhaven context (2-3 sentences)
    3. See the revenue picture (what the CFO thinks they know)
    4. Watch cost layers peel back progressively (deductions,
       fines, compliance, operational costs)
    5. Arrive at the contribution picture (dramatically different
       from step 3)
    6. Read the capital allocation implication
  - **Outcome:** Viewer understands and believes that dominant
    retail channels are far less profitable than revenue implies
  - **Covered by:** R1, R2, R3, R4, R5, R6

- F2. Drill-down verification flow
  - **Trigger:** Viewer clicks a channel element in any chart
  - **Actors:** A1, A2
  - **Steps:**
    1. Click a channel bar or segment
    2. Non-selected elements dim to 0.2-0.3 opacity
    3. Dark callout card appears inline showing line-item detail
    4. Viewer reads the breakdown supporting that layer's claim
    5. Click again or elsewhere to dismiss
  - **Outcome:** Viewer has verified the specific claim for that
    channel at that cost layer
  - **Covered by:** R7, R8, R9

---

## Requirements

**Narrative structure**

- R1. The page opens with a provocative, Economist-style headline
  claim — declarative, number-driven, derived from the actual data
  (not pre-committed before analysis).
- R2. A cold-start orientation (2-3 sentences) provides enough
  Cinderhaven context for viewers unfamiliar with the brand: scale,
  channel mix, and industry.
- R3. The narrative follows a progressive reveal structure: revenue
  picture first, then cost layers applied one at a time (gross margin,
  deductions, fines/compliance, operational costs), arriving at the
  contribution picture.
- R4. Each cost layer has its own narrative section with explanatory
  prose and a chart showing the impact on channel contribution.
- R5. The final section reframes the analysis as a capital allocation
  question — not just "here's the picture" but "here's what the
  allocation should look like given these margins."
- R6. All prose is Economist-style: sober, declarative, data-forward,
  no marketing voice, no hedging that softens a real finding.

**Charts and visualization**

- R7. Charts are SVG-based, using the Lailara design system: sequential
  teal palette (ranked by magnitude), Playfair Display for titles,
  Source Sans 3 for labels, horizontal-only gridlines, compact axis
  formatting.
- R8. Every chart uses click-to-pin interaction (not hover tooltips).
  Clicking a channel element pins a dark callout card showing line-item
  detail. Non-selected elements dim to 0.2-0.3 opacity with a 200ms
  ease-out transition.
- R9. Every data point has a text label. Charts are readable by
  non-data-scientist audiences without requiring interaction.
- R10. Charts at each narrative layer show the same channels but with
  the cumulative cost impact visible — the viewer watches the same
  bars transform as they scroll.

**Data integrity**

- R11. All headline numbers (revenue by channel, total contribution,
  deduction amounts) reconcile with sibling Cinderhaven projects —
  strict consistency with the shared data platform.
- R12. The analysis accounts for: deductions, OTIF fines, labeling
  penalties, compliance costs, and channel-specific operational
  overhead.
- R13. The data drives the story. If the numbers do not support the
  hypothesized conclusion (DTC more profitable per dollar than big
  retail), the narrative reports what the data actually shows.

**Interactivity**

- R14. Interactivity exists to support narrative claims — viewers
  drill into evidence behind each section's assertion. It does not
  enable free-form data exploration or parameter adjustment.
- R15. When a channel is pinned, the callout card shows the specific
  cost components contributing to that layer's reduction (e.g.,
  deduction types and amounts for the deductions layer).

**Deployment and accessibility**

- R16. Deployed as a static site (no live backend, no runtime database
  queries).
- R17. Print styles produce clean output: white background, SVG charts
  render as vectors, interactive controls hidden.
- R18. Respects prefers-reduced-motion: number animations snap to final
  value, dim transitions are instantaneous.

---

## Acceptance Examples

- AE1. **Covers R3, R10.** Given a viewer scrolling from the revenue
  section to the deductions section, when the deductions layer chart
  renders, the viewer sees the same channels as the previous chart but
  with bars reduced by deduction amounts — the visual delta between
  the two charts IS the deductions impact.

- AE2. **Covers R8, R15.** Given a viewer looking at the deductions
  layer chart, when they click the Walmart bar, non-Walmart elements
  dim to 0.2 opacity over 200ms, and a dark callout card appears
  showing Walmart's deduction breakdown (short ship $X, labeling $Y,
  OTIF $Z, etc.).

- AE3. **Covers R11, R13.** Given that the Trade Spend Diagnostic
  establishes $1M/year in operational waste, when the channel
  profitability analysis computes total margin erosion across channels,
  the figures are expressible as a decomposition of the same total —
  not an independently computed contradictory number.

---

## Success Criteria

- A first-time viewer can state the central claim and one supporting
  insight within 90 seconds of landing on the page.
- The narrative persuades a skeptic: someone who initially rejects
  "your biggest channel is your least profitable" can follow the
  layered evidence and arrive at the conclusion themselves.
- A portfolio evaluator sees demonstrated skill in: analytical rigor,
  executive communication, data visualization, and interactive
  storytelling.
- Numbers pass a reconciliation check against all sibling projects
  without contradiction.

---

## Scope Boundaries

- Slide/PDF export (follow-on phase after web narrative is solid)
- Amazon as a channel
- Free-form dashboard exploration or parameter adjustment sliders
- Reshaping data to fit a preconceived conclusion
- Industry benchmark comparisons
- Live backend or runtime database queries
- Comparison to competitor brands or external datasets

---

## Key Decisions

- **Progressive reveal over channel-by-channel walkthrough:** The
  story is about transformation of the same picture, not comparison
  of independent profiles. Revenue → contribution is the arc.
- **Astro + React islands over full React SPA:** Narrative-first
  content benefits from static HTML with hydrated chart components.
  Better scroll performance, cleaner authoring in MDX.
- **D3 over Recharts:** Click-to-pin with dim transitions and
  Economist-style minimalism requires direct SVG control. Recharts
  would require fighting its defaults.
- **dbt mart (canonical) + local Python (presentation) for data
  pipeline:** Core contribution calculation lives in the shared
  platform for consistency. Narrative-specific layer breakdowns are
  local to this repo.
- **Dark callout card (inline) for drill-downs:** Matches Lailara
  design system tokens. Keeps viewer in reading flow. No navigation
  disruption.
- **Cloudflare Pages for hosting:** Consistent with sibling projects.
  Static site deploy, same infrastructure.

---

## Dependencies / Assumptions

- The cinderhaven-data-platform Postgres database is accessible and
  contains sufficient deduction granularity (type, amount, retailer)
  to support per-channel cost attribution across multiple cost
  categories.
- A new dbt mart (`mart_channel_contribution` or similar) will be
  added to the data platform repo before this project's analysis
  layer can produce canonical numbers.
- The Lailara design system tokens (colors, typography, interaction
  patterns) are implemented as CSS/design tokens consumable by this
  project.
- Sibling projects' published numbers (Trade Spend Diagnostic: $1M
  waste, 4pt gap; Deduction Recovery: $1.33M backlog) are stable and
  will not change during this build.

---

## Outstanding Questions

### Deferred to Planning

- [Affects R12][Resolved — verified] Deduction data has 10 types
  mapping to Layers 1-3. Layer 4 (operational overhead) requires
  estimation assumptions: labor rate (~$30-40/hr) and flat triage
  cost per non-disputed deduction. No data generator changes needed.

- [Affects R10][Needs research] What specific chart type best shows
  the progressive transformation (grouped bars, waterfall, stacked
  with peel-away, or something else)?
- [Affects R5][User decision] How directive should the capital
  allocation section be — qualitative reframe ("consider shifting
  investment") or quantitative recommendation ("shift X% from retail
  to DTC")?
- [Affects R7][Technical] How to implement self-hosted fonts (Playfair
  Display, Source Sans 3) in the Astro build pipeline?
