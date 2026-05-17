---
title: "feat: Build channel profitability narrative site"
type: feat
status: active
date: 2026-05-16
origin: docs/brainstorms/channel-profitability-narrative-requirements.md
---

# feat: Build channel profitability narrative site

## Summary

Implement the channel profitability analysis as an Astro static site
with D3/React chart islands embedded in MDX narrative sections. Data
flows from a new dbt mart (canonical contribution by channel) through
a Python export script (layered JSON) into build-time props passed to
interactive chart components. The progressive-reveal narrative uses
`client:visible` hydration so charts load as the reader scrolls.
Deploys to Cloudflare Pages.

---

## Problem Frame

See origin document for full problem narrative. In brief: Cinderhaven's
$25M revenue is distributed across 6 channels, but revenue share does
not reflect contribution share once deductions, fines, and compliance
costs are layered in. This site proves that claim with layered evidence
an executive can verify interactively.

---

## Requirements

- R1. Provocative Economist-style headline (number-driven, data-derived)
- R2. Cold-start orientation (2-3 sentences for unfamiliar viewers)
- R3. Progressive reveal: revenue → gross margin → deductions → fines →
  contribution
- R4. Each cost layer has narrative prose and a chart showing impact
- R5. Capital allocation reframe as closing section
- R6. Economist-style prose throughout
- R7. SVG charts with Lailara design system compliance
- R8. Click-to-pin interaction with dark callout card and dim transitions
- R9. Text labels on every data point; readable without interaction
- R10. Charts show same channels across layers (visual transformation)
- R11. Strict data consistency with sibling projects
- R12. Analysis accounts for deductions, fines, compliance, operational
  overhead
- R13. Data drives the story (no preconceived conclusions)
- R14. Interactivity supports narrative claims only
- R15. Drill-down callout shows specific cost components per layer
- R16. Static site deployment (no live backend)
- R17. Print styles (white bg, SVG vectors, hidden interactive controls)
- R18. Respects prefers-reduced-motion

**Origin actors:** A1 (Portfolio viewer), A2 (Fictional executive)
**Origin flows:** F1 (Primary reading flow), F2 (Drill-down verification)
**Origin acceptance examples:** AE1 (covers R3, R10), AE2 (covers R8,
R15), AE3 (covers R11, R13)

---

## Scope Boundaries

- Slide/PDF export (phase 2)
- Amazon as a channel
- Free-form dashboard exploration or parameter sliders
- Industry benchmark comparisons
- Live backend or runtime database queries
- Reshaping data to fit a preconceived conclusion

### Deferred to Follow-Up Work

- dbt mart unit tests beyond basic reconciliation (separate PR in
  cinderhaven-data-platform)
- Slide export pipeline (separate project arc after web narrative ships)

---

## Context & Research

### Relevant Code and Patterns

- `short-ship-cost/web/`: React + Vite + Recharts + Cloudflare Pages
  (sibling pattern — same deploy target, different framework)
- `short-ship-cost/scripts/export_json.py`: Python export producing
  9 pre-aggregated JSON files from SQLite
- `retailer-deduction-recovery/scripts/20_export_json.py`: Python
  export from PostgreSQL producing 3 denormalized JSON files
- Both siblings use `scripts/` → `public/data/` → runtime fetch
  pattern; this project uses build-time import instead (Astro SSG)
- `cinderhaven-data-platform/models/`: dbt models with staging +
  mart layers; new mart_channel_contribution will follow established
  patterns

### External References

- Astro: `client:visible` with rootMargin for scroll-deferred hydration
- D3 in React: useRef + useEffect pattern; D3 owns the DOM
- Astro static output: no adapter needed for Cloudflare Pages
- JSON imports at build time passed as props to islands
- Manual @font-face in `public/fonts/` + global CSS
- MDX content collections with glob loader for ordered sections

---

## Key Technical Decisions

- **Build-time JSON import (not runtime fetch):** Astro's SSG resolves
  data at build time and serializes into HTML as island props. Avoids
  loading states, fetch error handling, and extra network requests.
  Siblings use runtime fetch because they're React SPAs with no SSG
  option — not an intentional choice to emulate.
- **`client:visible` as default hydration:** Charts are below the fold
  in a scrollable narrative. Deferring hydration until scroll saves JS
  download and parse time for content above. Use rootMargin 200px to
  start hydration before the chart scrolls into view.
- **D3 owns the DOM (Approach A):** React renders `<svg>` container;
  D3 manages all child elements in useEffect. Required for click-to-pin
  with dim transitions — managing opacity state on many elements is
  natural in D3's selection model and awkward in declarative React.
- **Independent pin state per chart:** Each chart manages its own
  pinned element. No cross-chart linked selection (Lailara design
  system specifies per-element pin/dismiss, not global filtering).
- **Manual @font-face over Astro Fonts API:** 5 font files, simple
  enough. Avoid experimental API surface. Preload only above-fold
  fonts (Playfair 700, Source Sans 400).
- **Content collections for narrative ordering:** MDX files in
  `src/content/narrative/` with frontmatter `order` field. Provides
  type-safe schema and ordered rendering.

---

## Open Questions

### Resolved During Planning

- **Astro adapter needed?** No — static output mode, no server functions.
  Wrangler deploys `dist/` directly.
- **Nanostores needed?** No — pin state is local to each chart. No
  cross-chart shared state.
- **SSR compatibility with D3?** Not an issue — D3 code runs inside
  useEffect which only executes client-side after hydration.

### Deferred to Implementation

- **Exact chart type per layer:** Whether bars, waterfall, or stacked.
  Will be determined during U5 when seeing actual data shape.
- **Capital allocation section format:** Qualitative reframe vs.
  quantitative recommendation. Determined by what the data supports.
- **Operational overhead estimation:** Exact labor rate and flat triage
  cost per non-disputed deduction. Decided during U3 data export.

---

## Output Structure

```
channel-profitability-analysis/
  astro.config.mjs
  package.json
  wrangler.jsonc
  tsconfig.json
  public/
    fonts/
      playfair-display-400.woff2
      playfair-display-700.woff2
      source-sans-3-400.woff2
      source-sans-3-600.woff2
      source-sans-3-700.woff2
  src/
    components/
      charts/
        ChannelChart.tsx
        CalloutCard.tsx
        chartUtils.ts
    content/
      narrative/
        01-headline.mdx
        02-revenue.mdx
        03-deductions.mdx
        04-fines-compliance.mdx
        05-operational.mdx
        06-contribution.mdx
        07-allocation.mdx
      config.ts
    data/
      channels.json
      layers.json
    layouts/
      NarrativeLayout.astro
    pages/
      index.astro
    styles/
      fonts.css
      global.css
      print.css
  scripts/
    export_data.py
    requirements.txt
  docs/
    brainstorms/
    plans/
```

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance
> for review, not implementation specification. The implementing agent
> should treat it as context, not code to reproduce.*

```
Data Flow:
  cinderhaven-data-platform (Postgres)
    → dbt mart_channel_contribution (canonical numbers)
    → Python export_data.py (queries mart + fact tables)
    → src/data/*.json (layered breakdown per narrative section)
    → Astro build imports JSON
    → Passes data as props to React/D3 chart islands
    → Static HTML + hydrated islands deployed to Cloudflare Pages

Narrative Flow (user scrolls):
  [Headline claim] → [Context] → [Revenue chart]
    → [Deductions chart] → [Fines chart] → [Operational chart]
    → [Contribution chart] → [Allocation reframe]

Interaction Flow (user clicks channel bar):
  Click → setState(pinnedChannel)
    → D3 dims non-pinned to opacity 0.2 (200ms ease-out)
    → CalloutCard renders with layer-specific breakdown
    → Click again → clear pin → restore opacity
```

---

## Implementation Units

### U1. Project scaffolding

**Goal:** Astro project with React + MDX integrations, font setup,
Lailara design tokens, and Cloudflare Pages deploy config. A "hello
world" that builds and deploys.

**Requirements:** R16, R17, R18

**Dependencies:** None

**Files:**
- Create: `package.json`
- Create: `astro.config.mjs`
- Create: `tsconfig.json`
- Create: `wrangler.jsonc`
- Create: `src/layouts/NarrativeLayout.astro`
- Create: `src/pages/index.astro`
- Create: `src/styles/fonts.css`
- Create: `src/styles/global.css`
- Create: `src/styles/print.css`
- Create: `public/fonts/` (5 woff2 files)
- Create: `src/content/config.ts`

**Approach:**
- `npm create astro@latest` then add React + MDX integrations
- Static output mode, no adapter
- Global CSS implements Lailara tokens (colors, typography, spacing)
- Print stylesheet: white bg, hidden interactive controls, SVG vector
- NarrativeLayout: max-width 900px, section gap 60px, font preloads
- Content collection schema: `{ title, order, section }` per MDX file
- Wrangler config: static assets from `dist/`

**Patterns to follow:**
- Lailara design system in shared CLAUDE.md (colors, type scale,
  layout tokens)
- `short-ship-cost/web/package.json` for Cloudflare/Wrangler setup

**Test scenarios:**
- Happy path: `npm run build` produces `dist/` with HTML, CSS, font
  files
- Happy path: `wrangler pages dev dist` serves the page locally
- Happy path: Playfair Display renders in headings, Source Sans 3 in
  body (visual check)
- Edge case: prefers-reduced-motion media query is present in CSS
- Edge case: Print stylesheet applies white background, hides
  interactive elements

**Verification:**
- Built site renders in browser with correct typography and colors
- Lighthouse audit shows no font-related CLS (preload working)
- Print preview shows clean output

---

### U2. dbt mart: channel contribution calculation

**Goal:** Add `mart_channel_contribution` model to the
cinderhaven-data-platform repo. Single source of truth for
contribution by channel, reconciled with sibling projects.

**Requirements:** R11, R12, R13

**Dependencies:** None (parallel with U1)

**Files:**
- Create: `models/marts/mart_channel_contribution.sql` (in
  cinderhaven-data-platform repo)
- Create: `models/marts/mart_channel_contribution.yml` (schema + tests)

**Approach:**
- Join: fct_orders (revenue) + dim_retailers (channel) + fct_deductions
  (by type: short_ship, label_fine, pallet_fine, late_delivery, etc.)
  + fct_shipments (compliance flags) + promotions (promo costs)
- Group by retailer/channel with columns: gross_revenue,
  cost_of_goods, trade_deductions, compliance_fines, labeling_fines,
  operational_overhead_estimate, net_contribution
- Operational overhead: estimate from disputes.labor_hours where
  available, flat rate per non-disputed deduction otherwise
- Validate: total deductions across channels must reconcile with
  Trade Spend Diagnostic's $1M waste figure (or be expressible as
  a decomposition of it)

**Patterns to follow:**
- Existing mart models in `cinderhaven-data-platform/models/marts/`
- dbt schema YAML conventions in that repo

**Test scenarios:**
- Happy path: mart builds without errors on `dbt run`
- Happy path: total revenue across channels sums to ~$25M (matches
  established figure)
- Integration: deduction totals by type reconcile with
  fct_deductions aggregate
- Edge case: DTC channel has zero deductions/fines (no retailer
  relationship costs)
- Edge case: operational overhead estimate produces reasonable FTE
  equivalents (not absurd)

**Verification:**
- `dbt test` passes with no failures
- Revenue total matches $25M established across sibling projects
- Channel contribution percentages are defensible and surprising
  (the story exists in the data)

---

### U3. Python export pipeline

**Goal:** Script that queries the data platform and produces layered
JSON files for each narrative section. The progressive reveal requires
intermediate states (revenue only, revenue minus deductions, etc.).

**Requirements:** R3, R10, R11, R12

**Dependencies:** U2

**Files:**
- Create: `scripts/export_data.py`
- Create: `scripts/requirements.txt`
- Create: `src/data/channels.json`
- Create: `src/data/layers.json`

**Approach:**
- Connect to cinderhaven-data-platform Postgres (DATABASE_URL env var)
- Query mart_channel_contribution for canonical totals
- Query underlying fact tables for layer-by-layer breakdown:
  - Layer 0: revenue by channel
  - Layer 1: revenue minus COGS (gross margin)
  - Layer 2: gross margin minus deductions
  - Layer 3: minus fines/compliance
  - Layer 4: minus operational overhead (= net contribution)
- For each layer, include per-channel breakdown of what was subtracted
  (for drill-down callout cards)
- Output: `channels.json` (channel metadata + revenue), `layers.json`
  (array of layer objects, each with per-channel values and detail)
- Validate: final layer matches mart_channel_contribution totals

**Patterns to follow:**
- `retailer-deduction-recovery/scripts/20_export_json.py` (PostgreSQL
  connection, custom JSON serializer for Decimal/date)
- `short-ship-cost/scripts/export_json.py` (multi-file output, builder
  pattern)

**Test scenarios:**
- Happy path: script runs without error, produces valid JSON
- Happy path: channel names and retailer IDs match platform dimensions
- Integration: layer 4 (final contribution) matches mart totals exactly
- Edge case: DTC channel has no deduction/fine layers (passes through
  unchanged)
- Error path: DATABASE_URL not set produces clear error message

**Verification:**
- JSON files parse without error
- Final-layer contribution totals match dbt mart query results
- Total revenue sums to ~$25M

---

### U4. Chart system: D3 React component + interaction

**Goal:** Reusable chart component implementing Lailara design system
with click-to-pin interaction, dim transitions, and dark callout card.
This is the shared foundation all narrative sections use.

**Requirements:** R7, R8, R9, R10, R14, R15, R18

**Dependencies:** U1

**Files:**
- Create: `src/components/charts/ChannelChart.tsx`
- Create: `src/components/charts/CalloutCard.tsx`
- Create: `src/components/charts/chartUtils.ts`
- Test: `tests/components/ChannelChart.test.tsx`

**Approach:**
- ChannelChart: React component with `useRef` + `useEffect` for D3
- Props: `{ data, layerLabel, previousData? }` — current layer values
  plus optional previous layer for visual comparison
- D3 renders: horizontal bars per channel, sequential teal palette
  (darkest = largest), text labels on each bar, horizontal-only
  gridlines, compact y-axis formatting ($1.2M)
- Click handler: sets pinnedChannel state, D3 transitions non-pinned
  bars to opacity 0.2 (200ms ease-out), renders CalloutCard
- CalloutCard: positioned above chart, dark background (#1a1a1a),
  shows line-item breakdown for pinned channel at current layer
- chartUtils: scales, color assignment, number formatting, animation
  helpers
- prefers-reduced-motion: skip transitions, snap to final state

**Patterns to follow:**
- Lailara design system: sequential teal palette, Playfair Display
  for chart titles, Source Sans 3 12px for axis labels, 2px border
  radius
- D3 selection.join() for enter/update/exit (prevents duplicate
  elements on re-render)

**Test scenarios:**
- Happy path: component renders SVG with correct number of bars
  matching channel count
- Happy path: clicking a bar sets pinned state and renders CalloutCard
- Happy path: clicking the same bar again clears pin and restores
  opacity
- Edge case: clicking a different bar while one is pinned swaps the
  pin
- Edge case: prefers-reduced-motion query present — transitions are
  instantaneous
- Edge case: channels with $0 value at a given layer still render
  (labeled "—" or "$0")
- Integration: Covers AE2. Click Walmart bar → non-Walmart dims to
  0.2 ��� dark callout shows deduction breakdown

**Verification:**
- Chart renders with correct Lailara colors and typography
- Click-to-pin interaction works (pin, swap, dismiss)
- CalloutCard shows correct data for pinned channel
- No duplicate SVG elements on React re-render

---

### U5. First vertical slice: Revenue + Deductions sections

**Goal:** Complete end-to-end proof of the pipeline: two MDX narrative
sections with working charts, real data, prose, and interaction. If
this works, the remaining sections are repetition.

**Requirements:** R1, R2, R3, R4, R6, R9, R10, R14

**Dependencies:** U3, U4

**Files:**
- Create: `src/content/narrative/01-headline.mdx`
- Create: `src/content/narrative/02-revenue.mdx`
- Create: `src/content/narrative/03-deductions.mdx`
- Modify: `src/pages/index.astro` (render content collection in order)

**Approach:**
- 01-headline: provocative claim derived from actual data (e.g.,
  "Walmart takes 50% of revenue and X% of contribution"). Written
  AFTER seeing the data from U3.
- 02-revenue: brief Cinderhaven orientation + revenue chart showing
  channel mix. This is the "what you think you know" baseline.
- 03-deductions: prose explaining deduction mechanics + chart showing
  revenue minus deductions. The first "wait, what?" moment.
- Each MDX file imports ChannelChart and passes layer-appropriate data
- index.astro renders sections in order using content collection query
- Verify: the visual delta between revenue chart and deductions chart
  tells the story (Covers AE1)

**Execution note:** Write prose AFTER the chart renders with real data.
The headline and framing should respond to what the numbers actually
show, not be pre-written.

**Patterns to follow:**
- Economist article structure: claim → evidence → insight
- Lailara voice: sober, declarative, data-forward

**Test scenarios:**
- Happy path: Covers AE1. Revenue section shows full bars; deductions
  section shows same channels with reduced bars — visual delta is the
  deductions impact
- Happy path: prose reads as Economist-style (no jargon, no marketing
  voice)
- Happy path: chart data matches JSON export (no transformation bugs)
- Integration: clicking a bar in the deductions chart shows deduction
  type breakdown (short_ship $X, label_fine $Y, etc.)
- Edge case: DTC has no deductions — bar unchanged between sections

**Verification:**
- Two narrative sections render in correct order with working charts
- Interactive drill-down shows correct data
- Pipeline proves out: dbt → Python → JSON → Astro build → chart
- A reader can follow the story from revenue to deductions without
  confusion

---

### U6. Remaining narrative sections

**Goal:** Complete the progressive reveal: fines/compliance layer,
operational overhead layer, final contribution picture.

**Requirements:** R3, R4, R5, R6, R10, R12

**Dependencies:** U5

**Files:**
- Create: `src/content/narrative/04-fines-compliance.mdx`
- Create: `src/content/narrative/05-operational.mdx`
- Create: `src/content/narrative/06-contribution.mdx`
- Create: `src/content/narrative/07-allocation.mdx`

**Approach:**
- 04-fines: OTIF penalties + labeling/pallet fines. Chart shows
  gross-minus-deductions further reduced by compliance costs.
- 05-operational: triage labor, dispute handling costs (estimated).
  Chart shows the operational overhead layer.
- 06-contribution: the final picture. Side-by-side or overlay showing
  revenue share vs. contribution share — the punchline.
- 07-allocation: capital allocation reframe. Not a chart section but
  a prose conclusion that answers "so what do you do about this?"
  Qualitative or quantitative depending on what the data supports.
- Each section follows the pattern established in U5

**Patterns to follow:**
- Structure from U5 (MDX + ChannelChart + prose pattern)
- Each section's prose responds to what the chart reveals

**Test scenarios:**
- Happy path: all 4 sections render in order with correct data
- Happy path: Covers AE3. Final contribution figures reconcile with
  Trade Spend Diagnostic ($1M waste is decomposable from these numbers)
- Happy path: progressive reveal is visually clear — bars shrink at
  each layer
- Edge case: some channels may have zero in certain cost categories
- Integration: drill-down at each layer shows the appropriate cost
  breakdown for that layer (fines layer shows fine types, not deduction
  types)

**Verification:**
- Full narrative reads as a coherent story from top to bottom
- Final contribution numbers match dbt mart exactly
- Capital allocation section provides a clear "so what" without
  prescribing a specific dollar reallocation (unless data supports it)

---

### U7. Polish and deploy

**Goal:** Production-ready deployment with print styles, accessibility,
performance optimization, and Cloudflare Pages deploy.

**Requirements:** R16, R17, R18

**Dependencies:** U6

**Files:**
- Modify: `src/styles/print.css` (finalize print rules)
- Modify: `src/layouts/NarrativeLayout.astro` (meta tags, OG image)
- Modify: `wrangler.jsonc` (final deploy config)
- Modify: `package.json` (deploy scripts)

**Approach:**
- Print: @page letter size, 0.6in margins, running footer (brand +
  page counter), charts render as SVG vectors
- Accessibility: focus-visible styles (2px solid, 2px offset),
  aria-labels on interactive chart elements, reduced-motion honored
- Performance: verify font preloading, check bundle size of chart
  islands, confirm `client:visible` defers correctly
- Deploy: `npm run build && wrangler pages deploy dist`
- Verify in browser: golden path scroll, each chart's interaction,
  print preview

**Patterns to follow:**
- Lailara print spec (running footer, 9pt Source Sans 3, #555)
- Lailara focus-visible spec

**Test scenarios:**
- Happy path: site builds without warnings, deploys to Cloudflare
- Happy path: print preview shows clean single-column layout with
  all charts visible as SVG
- Edge case: reduced-motion — no animations fire, charts render
  immediately in final state
- Edge case: keyboard navigation — Tab through chart elements,
  Enter/Space to pin
- Integration: full page scroll — charts hydrate as they enter
  viewport, no layout shift

**Verification:**
- Deployed to Cloudflare Pages, accessible via URL
- Lighthouse performance score > 90
- Full narrative reads correctly in browser and print
- All interactive elements work with mouse and keyboard

---

## System-Wide Impact

- **Interaction graph:** Chart component click handlers manage local
  pin state only. No cross-component side effects, no global state
  mutations.
- **Error propagation:** Build-time failures (missing JSON, broken MDX)
  surface at `astro build`. No runtime error paths in production (static
  site with pre-resolved data).
- **State lifecycle risks:** None — no database, no sessions, no cache.
  Static files served from CDN.
- **API surface parity:** N/A — no API.
- **Integration coverage:** The critical integration is the data pipeline
  (dbt → Python → JSON → Astro build → chart render). U5 proves this
  end-to-end before committing to remaining sections.
- **Unchanged invariants:** Sibling projects' published numbers remain
  unchanged. This project reads from the shared platform but does not
  modify it (the dbt mart is additive).

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Data lacks surprise (deductions don't dramatically change the picture) | Run U3 export first; if the story isn't there, pivot narrative framing before investing in polish |
| dbt mart reconciliation fails (numbers don't match siblings) | Validate in U2 against known Trade Spend Diagnostic totals before proceeding |
| D3 + React + Astro hydration conflict | U4 proves this works before content is written; `client:visible` avoids SSR issues |
| Operational overhead estimation is too speculative | Label it clearly in narrative as estimated; document assumptions in footnotes |
| Large JSON payload slows build or increases page weight | Split by layer if needed; current estimate (~50-100KB total) is well within bounds |

---

## Sources & References

- **Origin document:** [channel-profitability-narrative-requirements.md](docs/brainstorms/channel-profitability-narrative-requirements.md)
- Sibling pattern: `short-ship-cost/web/` (React + Vite + Cloudflare)
- Sibling pattern: `retailer-deduction-recovery/scripts/20_export_json.py` (Postgres export)
- Data source: `cinderhaven-data-platform/models/` (dbt marts)
- Astro docs: client directives, content collections, MDX integration
- Lailara design system: shared `~/projects/active/CLAUDE.md`
