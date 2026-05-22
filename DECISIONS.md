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

### 2026-05-17 — Data export uses generate_json.py with embedded constants
- **Why:** Live DB connection from export scripts is fragile on Windows (password management, flyctl proxy). Extracting data via piped SQL to `flyctl postgres connect`, then embedding in a Python script that generates JSON, is reproducible without DB access.
- **Scope:** Any re-export of channels.json, layers.json, trends.json
- **Do not:** Rely on `scripts/export_data.py` (the old live-connection approach) without first solving the password problem

---

## Visualization

### 2026-05-16 — Interactivity proves claims, not explores data
- **Why:** The piece is a guided narrative for executives. Click-to-pin drill-downs let skeptics verify each claim. Free-form exploration would undermine the narrative authority and balloon scope.
- **Scope:** All interactive elements in the deliverable
- **Do not:** Add filters, parameter sliders, or "explore your own view" features. If a viewer can change the story, the story isn't being told.

---

### 2026-05-17 — Quarterly trend margin excludes fines and operational overhead
- **Why:** Compliance fines and operational overhead are reported with quarterly lags and would produce misleading quarter-by-quarter trends. The annual contribution margin includes all five layers; the quarterly trend uses a three-layer formula (revenue − COGS − deductions) / revenue. This is disclosed in the trends section footnote.
- **Scope:** Trends section (06-trends.mdx) and trends.json generation
- **Do not:** Add fines or overhead to quarterly margin without solving the reporting-lag problem first.

### 2026-05-22 — Postgres is the SSOT; tools use JSON/SQLite intermediaries
- **Why:** User directive. The Postgres database on Fly.io (cinderhaven-db) is the single source of truth. generate_json.py embeds snapshot constants extracted from Postgres for offline use. Scripts must never modify Postgres.
- **Scope:** All data pipeline scripts (generate_json.py, refresh_data.py)
- **Do not:** Write to or modify the Postgres database. Pull from it only.

---

## Output Formats

### 2026-05-16 — Scrollable web narrative, not PDF or slides
- **Why:** The Economist-style narrative format with interactive drill-downs is the differentiator. PDF/slides are a follow-on phase after the web version is solid. The format itself — progressive disclosure through scroll + click-to-pin — is what makes this portfolio piece unique.
- **Scope:** Primary deliverable format
- **Do not:** Add PDF export to this arc. It's explicitly out of scope in PLAN.md.

---

## Writing & Voice

### 2026-05-16 — Economist style, no marketing voice
- **Why:** The narrative targets executives who are skeptical of consultant jargon. Sober, declarative, data-forward prose builds credibility. Marketing voice ("unlock value," "drive synergy") undermines it. The data leads; the prose follows.
- **Scope:** All MDX narrative sections
- **Do not:** Hedge findings or soften conclusions. If the data says a channel is underperforming, say so directly.

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
