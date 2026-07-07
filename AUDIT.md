# Project Audit (Historical — May 2026)

> **Note:** This audit was conducted 2026-05-17 against the original ~$24M
> dataset. The data has since been refreshed to ~$76.8M (2026-05-22).
> Clarification: the $76.8M is the 3yr cumulative total across FY2024–FY2026;
> the annual average is $25.6M/yr.
> Specific dollar figures and percentages below reflect the pre-refresh
> state. The structural findings (architecture, test gaps, pipeline design)
> informed subsequent improvements. See HANDOFF.md for current state.

## Phase 1: Baseline Assessment
**Date:** 2026-05-17
**Project:** Channel Profitability Analysis (Cinderhaven)

### What Was Intended

Channel-by-channel profitability narrative for Cinderhaven (~$24M specialty
food brand, fiscal year to March 2026). Scrollable, Economist-style web
narrative with interactive drill-downs answering: "Where is contribution
actually being earned across channels, and how should that reshape capital
allocation decisions?" Tier 1 flagship portfolio piece.

### What Exists Today

A fully built Astro + React/D3 web narrative deployed to Cloudflare Pages.
8 narrative sections with interactive charts, click-to-pin callout cards,
and contribution margin tables. 11 channels analyzed across 5 cost layers
(COGS, trade deductions, compliance fines, operational overhead). Data
pipeline: SQL → embedded Python constants → JSON → MDX → React components.

All code is functional — builds, deploys, renders. PR #1 merged to main.

### Tech Stack

| Component | Choice |
|---|---|
| Framework | Astro 5.9 (static site, React islands) |
| Charts | D3 v7 + React 19 |
| Content | MDX narrative sections |
| Data pipeline | Python script with embedded constants → JSON |
| Deployment | Cloudflare Pages (via Wrangler) |
| Fonts | Self-hosted Playfair Display + Source Sans 3 |
| Types | TypeScript |

### Project Health Indicators

- **Activity:** Active — 23 commits over 2 days (May 16–17, 2026), single contributor
- **Documentation:** Good — CLAUDE.md, PLAN.md, HANDOFF.md, DECISIONS.md, FAILURES.md, requirements doc, implementation plan all present and maintained
- **Test coverage:** None — no test files exist in `tests/`
- **Dependencies:** Current (all latest major versions)
- **Data freshness:** Stale — embedded constants in `generate_json.py` extracted from DB on May 17, 2026. User reports upstream data platform has since added many more rows and tables.

### Gap Analysis

**Intended vs. Actual:**
- [DONE] Scrollable narrative with interactive charts ✓
- [DONE] All 11 channels analyzed ✓
- [DONE] Economist-style voice ✓
- [DONE] Lailara design system applied ✓
- [GAP] `/ce:review` not yet run (PLAN.md shows incomplete)
- [GAP] `/qa` browser testing not yet run
- [GAP] No automated tests
- [GAP] Data may be stale — upstream DB has grown since last export

**Critical concern (user-flagged):** The upstream data source
(cinderhaven-data-platform) has had many more rows and tables added.
The math and analysis in this project may no longer reflect the current
state of the data. Specifically:
1. `generate_json.py` uses hardcoded constants extracted from a DB snapshot
2. New rows could change aggregated figures (revenue, deductions, fines)
3. New tables could introduce cost categories not currently captured
4. The narrative prose makes specific numerical claims that would break if data shifts

### Audit Motivation

Verify data integrity after upstream schema/data changes. Ensure the math
and analysis still make sense given the expanded dataset. The concern is
not the code or design — it's whether the numbers driving the narrative
are still correct.

---

## Phase 2: Internal Review
**Date:** 2026-05-17
**Dimensions reviewed:** Code quality, Architecture, Tests, Documentation, Performance, Security, UX, DevEx

### Top Opportunities (by leverage)

| # | Finding | Dimension | Impact | Effort | Leverage | Severity |
|---|---------|-----------|--------|--------|----------|----------|
| 1 | Meta description says "$32M" — actual revenue is $23.9M | UX | 4 | 1 | 4.0 | critical |
| 2 | No prose-vs-data validation — hardcoded claims in MDX can silently drift from data | Tests | 5 | 2 | 2.5 | critical |
| 3 | No automated data refresh — embedded constants in generate_json.py require full manual re-extraction from DB | Architecture | 5 | 3 | 1.7 | critical |
| 4 | DTC quarterly trend data is all zeros — structurally absent, potentially confusing | UX/Data | 3 | 2 | 1.5 | important |
| 5 | Two competing export scripts with no clear lifecycle | Architecture | 3 | 2 | 1.5 | important |
| 6 | Zero test coverage — no automated way to catch regressions | Tests | 4 | 3 | 1.3 | important |
| 7 | Whole Foods trade deduction rate: data says 18.2%, prose says 18.1% | Data | 2 | 1 | 2.0 | minor |
| 8 | TrendChart interface has unused `start_date` field not present in data | Code Quality | 1 | 1 | 1.0 | minor |
| 9 | Full D3 import (~70KB gzip) when only 5 submodules used | Performance | 2 | 2 | 1.0 | minor |
| 10 | No CI/CD pipeline — deploy is manual only | DevEx | 2 | 2 | 1.0 | minor |

### Detailed Findings

#### Data Integrity (the user's core concern)

**Internal math is consistent.** Every prose claim was verified against the
JSON data files:

| Claim | Verified Value | Status |
|---|---|---|
| Total revenue ~$24M | $23,915,660.92 | PASS |
| Trade deductions $3.1M | $3,104,892.76 | PASS |
| Compliance fines $778K | $778,061.10 | PASS |
| Operational overhead $324K | $324,255.75 | PASS |
| Spoilage $527K | $527,030.13 | PASS |
| Label fines $106K | $106,416.46 | PASS |
| Unclassified $1.2M | $1,177,898.63 | PASS |
| Promo billbacks $1.7M | $1,660,204.41 | PASS |
| DTC margin 73.2% | 73.2% | PASS |
| Walmart margin 21.1% | 21.1% | PASS |
| Walmart trade ded rate 15.1% | 15.1% | PASS |
| Whole Foods trade ded rate 18.1% | 18.2% | MINOR DRIFT (rounding) |

**However:** All these values derive from hardcoded constants in
`generate_json.py`, not from live queries. If the upstream DB has changed,
these numbers are stale. The internal consistency only proves the pipeline
doesn't corrupt data — it says nothing about whether the data still matches
the source.

**Specific upstream risks:**
1. New orders within the fiscal year window → revenue/COGS shift
2. New deduction records → deduction totals change
3. New channels added → 11-channel assumption breaks
4. New deduction types → silently excluded (only 9 recognized)
5. COGS ratios recalculated → all margin figures shift
6. DTC revenue recalculated → the "$1.3M / 73%" claim moves

#### Architecture

- **Fragile data pipeline (critical).** `generate_json.py` embeds raw numbers
  as Python constants. Any upstream change requires: connect to DB → run SQL
  → copy results → paste into Python → run script → check prose. Six manual
  steps with no safety net. `export_data.py` exists as a live-query
  alternative but doesn't support fiscal year filtering or trends, and has
  the Windows/flyctl password problem documented in FAILURES.md.
- **Two export scripts (important).** `export_data.py` (live connection,
  incomplete) and `generate_json.py` (embedded constants, complete) serve
  overlapping purposes. Neither validates against the other. A future
  maintainer won't know which to trust.
- **DTC estimation (important).** DTC revenue is "estimated as 1/3 of 3-year
  mart total" because DTC orders aren't in fct_orders. This ratio will drift
  as the 3-year window shifts.

#### Code Quality

- Code is clean and consistent throughout. Components follow clear patterns.
- Lailara design system tokens applied correctly to CSS and inline styles.
- One dead TypeScript field: `TrendChart.tsx:18` declares `start_date: string`
  in the `TrendQuarter` interface but no such field exists in `trends.json`.
- Inline styles in React components (CalloutCard, MarginTable) are acceptable
  for this project size but would become maintenance overhead if the design
  system evolved.

#### Tests

- **Zero test files exist.** The `tests/` directory is empty.
- No build-time assertions that JSON files are internally consistent.
- No snapshot tests for expected data ranges.
- No automated check that prose numerical claims match computed values.
- The `scripts/verify_math.py` file (created during this audit) is the first
  validation of prose-vs-data — it should be kept and expanded.

#### Documentation

- Project documentation (CLAUDE.md, PLAN.md, HANDOFF.md, DECISIONS.md,
  FAILURES.md) is thorough and well-maintained.
- No README explaining how to refresh data end-to-end for a new contributor.
- The brainstorm and plan docs in `docs/` provide good historical context.

#### Performance

- Full D3 import instead of tree-shaking individual modules. Adds ~70KB gzip
  to the client bundle. Not critical for a portfolio piece but easy to fix.
- `client:visible` hydration on all chart components is correct — no
  unnecessary JS loaded upfront.
- Static build with no runtime SSR — performance ceiling is high.

#### Security

- **No issues.** Static site with no user input, no auth, no API calls, no
  dynamic content. Attack surface is essentially zero. Wrangler config is
  clean. No secrets in the repo.

#### UX

- **Meta description says "$32M" (critical).** `NarrativeLayout.astro:15`
  contains `a $32M specialty food brand` — this is a stale figure from before
  the analysis was scoped to fiscal year. Should be ~$24M (or removed).
- **DTC absent from trend charts** with $0 revenue in all quarters. The prose
  correctly notes "DTC margins hold steady at 73% year-round" but this claim
  is derived from annual data, not quarterly tracking. If a reader looks at
  the trend chart expecting to see DTC, they'll be confused.
- Accessibility is solid: aria-labels on SVG charts, keyboard navigation on
  bars, focus-visible outlines, reduced-motion support.
- Print CSS handles page margins, running footer, and vector chart rendering.
- Mobile breakpoint at 640px with appropriate font scaling.

#### DevEx

- Build: `npm run build` works cleanly.
- Deploy: `npm run deploy` handles build + wrangler in one step.
- Data refresh: painful multi-step manual process (fly proxy → SQL → edit
  Python → run script → rebuild → deploy). No single command refreshes data.
- No linter or formatter configured. Code is consistent by convention.
- No CI/CD — a broken build wouldn't be caught until manual deploy.

### Summary

The project's code and design are solid — well-structured, consistent, and
faithful to the Lailara design system. The internal math checks out: every
prose claim aligns with the JSON data within acceptable rounding.

The vulnerability is structural: the entire analysis sits on hardcoded
constants extracted from a DB snapshot. There is no automated way to detect
when upstream data changes invalidate the narrative. The highest-leverage
fixes are: (1) fix the $32M meta tag (30 seconds), (2) build a data
validation test that catches prose/data drift, and (3) create a reliable
single-command data refresh path from the live DB.

---

## Phase 3: Landscape Scan
**Date:** 2026-05-17
**Category:** CPG channel profitability narratives — data-driven analyses answering "where is contribution margin earned by channel" for consumer packaged goods brands

### Competitors / Similar Projects

| # | Name | Type | Description | Traction |
|---|------|------|-------------|----------|
| 1 | Vividly (fka Cresicor) | SaaS | Trade spend analytics + deduction management for CPG. Dashboard-first, segmented by customer/product/SKU. | G2/Gartner reviewed 2026, $700K avg deduction recovery claimed |
| 2 | SupplyPike (SPS Commerce) | SaaS | Deduction dispute automation — shortage deductions, compliance chargebacks, co-op overbillings. | $1B+ recovered, flat-rate pricing |
| 3 | CPGvision | SaaS | Revenue Growth Management platform: TPM, TPO, AI scenario planning. Role-segmented dashboards (Executive/Sales/Finance). | Enterprise tier, persona-based views |
| 4 | Visualfabriq | SaaS | Enterprise "agentic integrated revenue management" — RGM + commercial IBP + TPO. Account/channel-level profitability. | VC-backed, enterprise pricing |
| 5 | Crisp | SaaS/Data | Retail data aggregation from 40+ retailers (POS, inventory, supply chain). AI Agent Studio launched 2025. | $26M raised late 2025 |
| 6 | Daasity | SaaS | Omnichannel analytics for consumer brands — Shopify, Amazon, wholesale, retail. Customer-level profitability. | Mid-market CPG focus |
| 7 | McKinsey channel contribution framework | Consulting | Published CPG e-commerce profitability research: brick-and-mortar highest margin, DTC 40-60%, Amazon 10-20%. | Global consulting authority |
| 8 | CFO Pro Analytics framework | Reference | Five-layer CPG reporting: Channel P&L → Customer → SKU → Cohort → Cash Flow. Cost-layer methodology. | Published framework, no product |
| 9 | Endlesscommerce playbook | Reference | Contribution-margin-by-channel playbook with five-channel cost-layer peeling (DTC, Wholesale, FBA, Vendor, National Retail). | Written playbook |
| 10 | The Pudding | Data narrative | Canonical interactive scrollytelling (D3+Svelte). Cultural/social data, not financial. | High editorial reputation |

### Feature Matrix

| Feature | This Project | Vividly | SupplyPike | CPGvision | McKinsey | The Pudding |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| Channel segmentation | ✅ | ✅ | ❌ | ✅ | ✅ | ➖ |
| Cost-layer peeling (COGS→deductions→fines→overhead) | ✅ | 🟡 | ❌ | ✅ | ✅ | ➖ |
| Contribution margin by channel | ✅ | ✅ | ❌ | ✅ | ✅ | ➖ |
| Deduction breakdown by type | ✅ | ✅ | ✅ | 🟡 | ❌ | ➖ |
| Narrative / editorial framing | ✅ | ❌ | ❌ | ❌ | 🟡 | ✅ |
| Interactive scroll-driven charts | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Click-to-pin detail cards | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Actuals vs. plan/budget | ❌ | ✅ | ❌ | ✅ | ❌ | ➖ |
| SKU-level drill-down | ❌ | ✅ | 🟡 | ✅ | ❌ | ➖ |
| AI / scenario planning | ❌ | ❌ | ❌ | ✅ | ❌ | ➖ |
| Automated dispute filing | ❌ | ❌ | ✅ | ❌ | ❌ | ➖ |
| Live data connection | ❌ | ✅ | ✅ | ✅ | ➖ | ➖ |
| Multi-period trend tracking | ✅ | ✅ | ❌ | ✅ | ❌ | ➖ |
| Print/PDF output | ✅ | 🟡 | ❌ | 🟡 | ✅ | ❌ |
| Mobile responsive | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Accessibility (a11y) | ✅ | 🟡 | 🟡 | 🟡 | ❌ | ✅ |
| Executive-ready without explanation | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |

### Landscape Position

#### Table Stakes (standard in category)
All present in this project:
- Channel segmentation (retailer / distributor / DTC)
- Cost-layer peeling methodology
- Named metrics (contribution margin %, deduction rate)
- Channel-level gross-to-net breakdown

#### Where This Project Is Stronger
- **Narrative authority.** No SaaS tool in this space presents channel
  profitability as a guided narrative. Every competitor is a dashboard
  or operational workflow. This project tells a story that can be read
  by a non-technical executive without training.
- **Editorial quality.** Economist-style voice, self-hosted typography,
  design system consistency. Consulting deliverables are PDFs; SaaS tools
  are dashboards; nothing else combines analytical depth with editorial
  craft in an interactive web format.
- **Progressive disclosure.** Five-layer peeling revealed through scroll +
  click-to-pin interaction. Readers discover complexity at their own pace.
  Dashboards dump everything at once; consulting PDFs are linear.
- **Print compatibility.** SVG charts render as vectors, print CSS with
  running footers. None of the SaaS tools handle this.

#### Where This Project Is Weaker
- **No live data connection.** Every SaaS competitor refreshes automatically.
  This project requires manual re-extraction — the core vulnerability
  identified in Phase 2.
- **No SKU-level drill-down.** Analysis stops at channel level. Vividly and
  CPGvision go deeper to show which products are profitable within each
  channel.
- **No actuals vs. plan.** No budget comparison or forecast. The analysis
  is retrospective only.
- **No AI/optimization.** The category is moving toward "what should we do
  differently" via simulation. This project makes recommendations in prose
  but can't model scenarios.
- **Single dataset / point-in-time.** The narrative is a snapshot. SaaS tools
  update continuously and show trend alerts.

#### Unique Differentiators
- **Genre-defining.** Portfolio-quality CPG channel profitability narratives
  do not appear to exist as a public category. The combination of domain
  specificity + analytical depth + scroll narrative format is unoccupied.
- **Scroll-driven financial analysis.** Interactive scrollytelling exists
  (The Pudding, Nikkei) but none apply it to CPG operating data. This sits
  at the intersection of data journalism craft and CPG finance — a gap no
  one else fills.
- **Cost-layer waterfall as scroll experience.** The progressive reveal of
  COGS → deductions → fines → overhead as a narrative arc (not a static
  waterfall chart) is structurally novel.
- **Compliance fines as a visible cost layer.** Most tools bundle fines into
  "deductions" or ignore them. Separating label fines, spoilage, and late
  delivery as their own layer with per-channel detail is unusual.

#### Category Trends
- SaaS is moving toward **AI-driven scenario planning** and **agentic
  automation** (CPGvision, Visualfabriq, Crisp AI Agent Studio)
- **Real-time data infrastructure** is the investable trend ($26M into Crisp)
  — the analytics layer on top remains thin
- **Scroll-driven financial narratives** are emerging in corporate annual
  reports (BMW, Adidas 2024, Red Dot Award winners) but haven't penetrated
  CPG operating analytics yet
- **Role-segmented views** (executive vs. practitioner) are appearing in
  enterprise tools — suggesting the "one analysis, multiple audiences"
  problem is real and unsolved

### Summary

This project occupies a genuinely uncontested position: no existing tool
or published work combines CPG channel profitability analysis at this
analytical depth with an interactive scroll-driven narrative format. The
SaaS competitors are operational dashboard tools; the consulting frameworks
are static PDFs; the data journalism precedents don't touch CPG finance.
The format itself — not just the analysis — is the differentiator.

The weakness is operational: static data, no SKU depth, no scenario
modeling. These are not competitive threats for a portfolio piece (the
audience isn't choosing between this and a $50K SaaS subscription) but
they represent the ceiling on analytical credibility if the data goes stale.

---

## Phase 4: Differentiation & Next Moves
**Date:** 2026-05-17

### Cross-Reference Summary

The internal vulnerability (stale hardcoded data) and the competitive
weakness (no live data connection) are the same problem viewed from
different angles. Fixing it serves both: internally it restores
credibility; competitively it closes the one gap that actually matters
for a portfolio piece. SaaS competitors have live connections because
they're operational tools — this project doesn't need real-time, but it
does need a reliable way to refresh when the source changes.

The project's genuine differentiators (narrative format, editorial quality,
progressive disclosure, cost-layer waterfall as scroll experience) are all
intact and uncontested. No investment is needed to maintain that advantage
— it's structural. What IS needed is ensuring the analytical foundation
beneath the narrative remains correct. A beautifully told story with wrong
numbers is worse than an ugly dashboard with right numbers.

The highest-leverage moves sit at the intersection of "fixes the user's
immediate concern" and "extends the competitive advantage." Specifically:
refreshing data from the current DB state (immediate), building validation
that catches drift automatically (foundational), and then — once the
foundation is solid — considering whether new tables in the upstream DB
enable deeper analysis that strengthens the narrative.

### Ranked Next Moves

| # | Move | Category | Strategic | Internal | Effort | Score | Description |
|---|------|----------|-----------|----------|--------|-------|-------------|
| 1 | Fix $32M meta tag | foundational | 1 | 4 | 1 | 5.0 | 30-second fix. Wrong number in search results / social cards. |
| 2 | Re-extract data from current DB | close gap | 4 | 5 | 2 | 4.5 | The user's stated concern. Connect to cinderhaven-db, re-run fiscal year queries, regenerate all 3 JSON files. Validates whether the narrative still holds. |
| 3 | Prose-vs-data validation test | foundational | 2 | 5 | 2 | 3.5 | Automated check that every hardcoded claim in MDX matches computed values from JSON. Catches drift on any future refresh. |
| 4 | DTC trend annotation | double down | 3 | 3 | 1 | 6.0 | Add explanatory note or flat-line visualization for DTC in trend charts. Strengthens progressive disclosure — readers don't wonder why DTC is missing. |
| 5 | Single-command data refresh script | foundational | 3 | 5 | 3 | 2.7 | Consolidate the two export scripts into one reliable path: query DB → generate JSON → validate → report diff. Unblocks all future refreshes. |
| 6 | Audit upstream for new channels/cost types | close gap | 4 | 4 | 2 | 4.0 | Check if the expanded DB has new channels or deduction types not captured in current analysis. If so, the 11-channel / 9-type assumption is wrong. |
| 7 | Investigate SKU-level data availability | leapfrog | 5 | 2 | 2 | 3.5 | If new tables in the data platform include SKU-level contribution, adding "within Walmart, which SKUs earn their shelf space?" would combine narrative format with analytical depth no one else offers in this form. |
| 8 | Consolidate export scripts | foundational | 1 | 4 | 2 | 2.5 | Merge export_data.py and generate_json.py into one script that handles fiscal year filtering, trends, and validation. |
| 9 | Add basic test coverage | foundational | 1 | 4 | 3 | 1.7 | JSON schema validation, math consistency checks, build-time assertions. |
| 10 | CI/CD pipeline | foundational | 1 | 3 | 2 | 2.0 | GitHub Actions: build on push, deploy on merge to main. Catches broken builds. |

### Recommended Sequence

**Immediate (this session / today):**
1. Fix $32M meta tag (30 seconds)
2. Re-extract data from current DB — validate whether numbers have changed
3. Audit upstream for new channels/cost types (can be combined with #2)

**Short-term (next session):**
4. If data changed: update JSON files, re-verify prose claims, fix any drift
5. Prose-vs-data validation test (so this never happens silently again)
6. DTC trend annotation
7. Consolidate into single-command refresh script

**Medium-term (after the narrative is correct and protected):**
8. Investigate SKU-level data for potential narrative expansion
9. Basic test coverage
10. CI/CD pipeline

The logic: get the data right first (the user's concern), protect it from
future drift (validation), then consider whether new data enables a
stronger narrative (SKU depth).

### What NOT to Do

- **Don't add actuals-vs-plan.** There's no budget data in the platform,
  and even if there were, budget comparison is a dashboard concern — it
  undermines narrative authority. The story says "this IS what happened,"
  not "this is how we did vs. expectations."

- **Don't add AI/scenario modeling.** The category is moving there, but
  this project's strength is explanatory clarity, not predictive power.
  Adding "what if we shift 10% to DTC" as a slider would turn a narrative
  into a tool and compete on SaaS competitors' home turf.

- **Don't add free-form exploration.** The interactivity (click-to-pin)
  supports claims; it doesn't replace the narrative with a dashboard.
  Adding filters or "build your own view" would destroy the editorial
  authority that makes this unique.

- **Don't chase real-time data.** A portfolio piece doesn't need live
  connections. It needs to be correct at publication time and have a
  reliable path to re-publish when data changes. That's the standard for
  journalism and consulting deliverables — match it, don't exceed it.

- **Don't add more channels just because they exist.** If the upstream
  DB now has Amazon or foodservice, evaluate whether including them
  strengthens or dilutes the narrative. More channels ≠ better analysis.
  The story is about contribution variance, not comprehensiveness.

- **Don't tree-shake D3 right now.** It's a real improvement but the
  effort-to-impact ratio is wrong while the data integrity question is
  unresolved. Fix data first; optimize bundle later.

---
