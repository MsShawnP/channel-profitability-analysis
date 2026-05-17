# Channel Profitability Analysis — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Channel-by-channel profitability analysis for Cinderhaven ($25M specialty
food brand) delivered as a scrollable, Economist-style web narrative with
interactive drill-downs. Tuned for executive communication. Data-driven
story — hypothesis is that dominant retail channels (Walmart, Costco) are
far less profitable than their revenue share implies once fines, deductions,
and compliance costs are accounted for. DTC (3% of revenue) serves as the
reference point that makes this margin erosion visible. The data leads.

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
- [ ] Run /ce:work to execute (start with U1 + U2 in parallel)

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

### [Date completed] — [Goal]
- Outcome: [what shipped or what was decided]
- Tag: [git tag if one was created]

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->
