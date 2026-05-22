# Channel Profitability Analysis — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Channel-by-channel profitability analysis for Cinderhaven (~$76.8M annual
revenue across 10 channels) delivered as a scrollable, Economist-style
web narrative with interactive drill-downs. Tuned for executive
communication. Data-driven story — distributors retain ~90% of revenue
after COGS, deductions, fines, and operational overhead. Retailers retain
80–83%. DTC retains 83% but at much smaller scale ($573K). The data leads.

## Why this arc, why now

Tier 1 flagship portfolio piece. First buyer-facing consumer of the
Cinderhaven Data Platform. Demonstrates ability to distill complex
financial data into clear executive-ready narrative.

Differentiation from Trade Spend Diagnostic: that project answers "how
much margin is leaking and where" (a diagnostic). This project answers
"given the true contribution by channel, where should capital go instead"
(a strategic recommendation). Same data, different question.

## Business question this arc answers

Where is contribution actually being earned across channels, and how
should that reshape capital allocation decisions?

## Constraints

- No Streamlit
- Lailara design system (Playfair Display + Source Sans 3, sequential teal palette, Economist chart rules)
- Strict data consistency with 4-5 sibling Cinderhaven projects
- Data source: cinderhaven-data-platform repo (synthetic)
- Tech stack: open (to be decided in /ce:brainstorm)
- Timeline: no hard deadline — excellence is the constraint

## Tasks

Work in vertical slices — one section/feature end-to-end before moving
to the next. Visualizations get reviewed in their own slice, not
deferred to a polish phase.

- [x] Run /clarify to scope the work
- [x] Run /office-hours to stress-test the idea
- [x] Run /plan-ceo-review for product gate
- [x] Run /plan-eng-review for architecture gate
- [x] Run /ce:brainstorm to spec the approach
- [x] Run /ce:plan to create implementation plan
- [x] Run /ce:work to execute (U1–U7 complete, data refreshed)
- [x] Fix analysis period (filter to trailing 12 months or reframe language)
- [x] Run /ce:review (reviewer ensemble) — 2026-05-17, 16 findings fixed
- [x] Run /qa (browser testing) — 2026-05-17, all checks pass

## Design notes

- Cold-start orientation: the deliverable needs a brief (2-3 sentence)
  Cinderhaven context at the top for viewers arriving without having seen
  the other portfolio projects. Enough to understand the brand, scale, and
  channel mix — then straight into the analysis.

## Out of scope for this arc

- Slide/PDF export (follow-on phase after web narrative is solid)
- Amazon as a channel
- Free-form dashboard exploration (interactivity supports narrative claims only)
- Reshaping data to fit a preconceived conclusion
- Industry benchmark comparisons (unless data platform already includes them)

## Definition of done for this arc

- [ ] Analysis is rigorous — accounts for fines, deductions, and channel-specific costs
- [ ] Numbers reconcile with sibling Cinderhaven projects (strict consistency)
- [ ] Narrative reads as Economist-style executive communication (no jargon, no hedging)
- [ ] Charts are polished per Lailara design system (not default/Excel-looking)
- [ ] Interactive drill-downs support each major claim
- [ ] A non-data-scientist executive could follow the story and act on it
- [ ] Deployed as a scrollable web page

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### 2026-05-17 — Channel Profitability Narrative
- Outcome: Economist-style scrollable narrative with interactive D3 charts, deployed to Cloudflare Pages. 8 sections covering revenue → contribution waterfall. Full data integrity audit, automated validation (30 checks), single-command refresh pipeline. 4-agent review ensemble, all findings addressed.
- URL: https://channel-profitability-analysis.pages.dev

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
