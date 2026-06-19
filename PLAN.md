# Channel Profitability Analysis — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Replace the static Economist-style prose report with an interactive
drill-down channel-analysis tool. Same business question ("where is
contribution earned, where should capital go"), fundamentally different
delivery. Cinderhaven, $25.6M/yr annual average across 10 channels.

Tier: Heavy

## Why this arc, why now

The static report was the v1 proof of concept. It proved the data story
works. But static prose with hardcoded figures breaks every time the
pipeline updates, the voice can't adapt to filtered views, and the
format doesn't let users interrogate the data. The redesign turns a
read-only report into a tool executives can use.

Still Tier 1 flagship portfolio piece. Still the first buyer-facing
consumer of the Cinderhaven Data Platform.

## Business question this arc answers

Where is contribution actually being earned across channels, and how
should that reshape capital allocation decisions?

## Architecture (from /clarify, 2026-06-19)

- **Drill-down model:** All Channels → Segment (Retail/Distribution/DTC)
  → Individual Channel. In-place content transitions with breadcrumb nav.
  Full interpretive prose at all 3 levels.
- **Time filtering:** 3 fiscal years (FY2024–FY2026), quarterly slices,
  and arbitrary custom date ranges. Default: FY2026.
- **Prose engine:** Rule-based dynamic generation. Every number and
  interpretive claim computed from filtered data at runtime. Economist
  voice via authored sentence templates with conditional logic. No static
  MDX prose survives.
- **Charts:** 7 types — waterfall, stacked bar, slope, heatmap,
  sparklines, bullet, Marimekko. All D3, all design-system-compliant,
  all filter-responsive. Single release, no phasing.
- **Frame:** Lailara design system port (header, footer, `--ll-*` tokens,
  layout contract).
- **Accessibility:** Accessible SVG baseline — aria-labels, hidden data
  table fallbacks, keyboard navigation.
- **Deploy:** Current site goes dark immediately (maintenance page at
  channels.lailarallc.com). Single release replaces it.

## Critical dependency — RESOLVED (2026-06-19)

Postgres data granularity for all 5 waterfall layers confirmed at
quarterly grain. Fines and overhead are in the same deduction tables as
trade deductions (`fct_retailer_deductions`, `fct_distributor_deductions`),
which have `deduction_date`. The v1 pipeline chose not to use quarterly
fines/overhead (DECISIONS.md: "reported with quarterly lags"), but the
underlying data supports it. COGS uses static ratios per channel — apply
to quarterly revenue for quarterly gross margin, or join `raw.sku_costs`
if time-varying COGS matters.

Note: DB password auth failed during scouting (2026-06-19). Findings
are derived from existing query patterns in `refresh_data.py`, not a
live query. Confirm live when auth is restored.

## Constraints

- No Streamlit
- Lailara design system (Playfair Display + Source Sans 3, sequential teal palette, Economist chart rules)
- Strict data consistency with sibling Cinderhaven projects
- Data source: Postgres on Fly.io (cinderhaven-db) — SSOT
- Stack: Astro 5.9 + React 19 + D3 v7 (carry forward from v1)
- Desktop/tablet target — no mobile-first
- No print stylesheet
- No PDF export
- No Amazon channel
- Single release — no phased launch
- Timeline: no hard deadline — excellence is the constraint

## Tasks

Work in vertical slices. Visualizations get reviewed in their own slice.

- [x] Run /clarify to scope the redesign — 2026-06-19
- [ ] Deploy maintenance page (take current site dark)
- [ ] Scout Postgres quarterly granularity for fines + overhead
- [ ] Run /office-hours to stress-test the redesign idea
- [ ] Run /plan-ceo-review for product gate
- [ ] Run /plan-eng-review for architecture gate
- [ ] Run /ce:brainstorm to spec the approach
- [ ] Run /ce:plan to create implementation plan
- [ ] Run /ce:work to execute
- [ ] Run /ce:review (reviewer ensemble)
- [ ] Run /qa (browser testing)

## Out of scope for this arc

- Slide/PDF export
- Amazon as a channel
- Mobile-first responsive design
- Print stylesheet
- LLM-generated prose (ruled out — rule-based engine chosen)
- Free-form dashboard exploration beyond the 3-level drill-down

## Definition of done for this arc

- [ ] 3-level drill-down works (All → Segment → Channel) with breadcrumb nav
- [ ] Time filtering works (FY, quarter, custom range) across all views
- [ ] Rule-based prose engine generates Economist-style interpretive text for all 3 levels
- [ ] All 7 chart types render with filtered data and design system tokens
- [ ] 5-layer waterfall (Revenue → COGS → Deductions → Fines → Net Contribution) at every level
- [ ] Lailara design system frame (header, footer, tokens, layout contract)
- [ ] Accessible SVG baseline (aria-labels, data table fallbacks, keyboard nav)
- [ ] Numbers reconcile with sibling Cinderhaven projects
- [ ] Deployed at channels.lailarallc.com replacing the maintenance page
- [ ] A non-data-scientist executive could drill down and act on findings

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### 2026-06-19 — Static Report (v1) — Complete, superseded by redesign
- Outcome: Economist-style scrollable narrative with interactive D3 charts. 8 sections, 5-layer waterfall, 30+ automated validation checks. Multiple data refreshes and reconciliation passes. All Heavy-tier gates passed.
- URL: https://channels.lailarallc.com (going dark — replaced by maintenance page during redesign)
- Superseded by: Interactive drill-down redesign (current arc)

### 2026-05-17 — Channel Profitability Narrative (original build)
- Outcome: Economist-style scrollable narrative with interactive D3 charts, deployed to Cloudflare Pages. 8 sections covering revenue → contribution waterfall. Full data integrity audit, automated validation (30 checks), single-command refresh pipeline. 4-agent review ensemble, all findings addressed.
- URL: https://channels.lailarallc.com

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

### 2026-05-22 — Improvement pass
- **Trigger:** User-initiated `/improve` after data refresh
- **What was reviewed:** Code quality (4-agent ensemble), security, data/analysis correctness (120 calculation checks), manual audit of all files
- **What was fixed:**
  - CRITICAL: DTC channel_type case mismatch (`"dtc"` → `"DTC"`) — live site showed empty DTC charts
  - CRITICAL: Rewrote `refresh_data.py` — was referencing non-existent tables/columns, now uses correct schema
  - CRITICAL: Rewrote `verify_math.py` — was using hardcoded stale values, now derives from JSON
  - CRITICAL: Rewrote `verify_roi.py` — was completely stale, now derives from JSON
  - IMPORTANT: README rewritten with correct revenue figure, setup, pipeline, and validation docs
  - IMPORTANT: CLAUDE.md Stack section filled in (was "TBD")
  - IMPORTANT: DECISIONS.md populated with 4 documented decisions
  - IMPORTANT: npm audit fix (ws vulnerability resolved; astro XSS deferred — breaking change, no user input)
  - NICE TO HAVE: .gitignore expanded (.wrangler/, *.sqlite, credentials, backups)
  - NICE TO HAVE: Security headers added (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy)
  - NICE TO HAVE: AUDIT.md marked as historical with note about data refresh
  - NICE TO HAVE: Trends/fiscal ~0.3% rounding gap confirmed as expected (different aggregation paths)
- **Deferred:** Astro major version upgrade (5.9→6.3) for XSS fix — breaking change, low risk for static site with no user input
- **Next review:** 2026-06-22

<!-- Entries are added by /improve — don't delete this section -->
