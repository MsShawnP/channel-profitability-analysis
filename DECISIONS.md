# Channel Profitability Analysis — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-16 — Astro + React/D3 islands (not React SPA)
- **Why:** Narrative-first content benefits from static HTML with hydrated chart components. Better scroll performance, cleaner MDX authoring, deferred hydration via `client:visible`. Siblings use React SPAs because they're interactive tools, not articles.
- **Scope:** Framework choice for this project's web deliverable
- **Do not:** Switch to a React SPA or Streamlit. If the framework needs to change, it's a full restart.

---

## Data & Schema

### 2026-05-16 — Canonical contribution in dbt mart, narrative layers in local Python
- **Why:** Strict consistency across 4-5 sibling projects requires a single source of truth for "contribution by channel." Narrative-specific intermediate views (revenue before deductions, after deductions, etc.) are presentation logic local to this repo.
- **Scope:** Data pipeline for this project; also affects cinderhaven-data-platform repo (new mart model)
- **Do not:** Compute canonical contribution numbers in a local script. If the number could be cited by another project, it belongs in the platform mart.

---

## Visualization

### 2026-05-16 — Interactivity proves claims, not explores data
- **Why:** The piece is a guided narrative for executives. Click-to-pin drill-downs let skeptics verify each claim. Free-form exploration would undermine the narrative authority and balloon scope.
- **Scope:** All interactive elements in the deliverable
- **Do not:** Add filters, parameter sliders, or "explore your own view" features. If a viewer can change the story, the story isn't being told.

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

---

## Writing & Voice

[Voice, style, terminology decisions specific to this project]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
