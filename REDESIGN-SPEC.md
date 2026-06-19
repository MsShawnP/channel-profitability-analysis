# Channel Profitability Analysis — Full Redesign Spec

**Repo:** `channel-profitability-analysis` (live at channels.lailarallc.com)
**Goal:** Convert the current static prose-with-charts report into an interactive, drill-down channel-analysis tool that fully adopts the Lailara design system. Flagship/showpiece quality.
**Stack (confirmed):** Astro 5.9 + @astrojs/react + @astrojs/mdx, React 19, D3 v7, static output, self-hosted fonts.

---

## Decisions already made (do not re-litigate)

- **Scope:** Full redesign (not a reskin). Content is strong and stays; the page reorganizes around visuals and becomes interactive.
- **Frame adoption:** Proper Astro port of lailara-frame — this becomes the first Astro reference consumer of the frame. NOT a minimal alias / hand-copy.
- **Charts:** D3 (house standard, consistent with the repo and the design system's chart guidance, best performance for these chart types). NOT Plotly. The waterfall is built custom from stacked bars (D3 has no native waterfall — this is the one accepted extra cost).
- **Time default:** Opens on the current fiscal year, **FY2026**.
- **Structure shift:** Visual-first. Each section = chart carries the data, tight prose interprets it. Inverts the current prose-first-with-charts-appended layout.

---

## 1. Frame port (the Astro adoption pattern)

This establishes how an Astro/MDX site wears the Lailara frame. Do it cleanly so the next Astro tool can copy it.

- **Vendor** `lailara-frame.css` + the `fonts/` directory into the Astro project's static assets. Vendor a tagged release — never live-link.
- **Replace** the hand-copied palette in `global.css` / `NarrativeLayout.astro` (`--color-*`, `--teal-*`, `--color-navy`) with the canonical `--ll-*` tokens from the frame. Remove the duplication — adopt, don't alias.
- **Port the shell markup** into `NarrativeLayout.astro`:
  - `.lailara-page` > `.lailara-header` (sticky, canvas bg, 1px London-85 bottom rule) with `.lailara-nav-inner` containing the `.lailara-wordmark` ("Lailara LLC") and `.lailara-tool-name` ("CHANNEL PROFITABILITY").
  - `.lailara-main` > `.lailara-container` (caps at 1200px, padding 48px 24px) wrapping content.
  - `.lailara-footer` (dark, London-10) with "Built by Lailara LLC".
- **Widths:** container `--ll-max-width: 1200px`; prose `--ll-body-max-width: 720px`. (Current site is 900px — widen it.)
- **Canvas:** `#f5f3ee` warm off-white — the brand signature. NOT pure white.
- **Shape/elevation:** 2px radius only; no drop shadows on content — depth via 1px London-85 borders, or full dark inversion for callout cards.

---

## 2. Landing view

Three columns, side by side — one per segment: **Retailers / Distributors / DTC**.

Each column contains:
- A **margin-contribution bar** (the headline %: Retailers ~50.6% / Distributors ~45.3% / DTC ~82.6%).
- Its own **small waterfall** showing how that segment arrives at its %: gross → −COGS → −trade deductions → −compliance fines → −dispute overhead → net contribution.

This makes the page's core thesis — *segments erode differently* — the first thing the user sees, with mechanism (waterfall) paired to result (bar), three-up.

---

## 3. Drill-down model (best practice: direct manipulation + discoverability)

**Path:** All → Segment → individual Channel (3 depths).

- **Click-to-drill** on the charts themselves (click a segment's chart → into that segment; click a channel → into that channel).
- **Breadcrumb** always visible and clickable to climb back: `All > Retailers > Walmart`.
- **Selector control** alongside (dropdown) so the drill is discoverable without the user guessing the charts are clickable.
- **Hover cue** (cursor change + subtle highlight) signaling clickability.

**What each level reveals:**
- **Segment** (e.g. Retailers): that segment's waterfall + its individual channels.
- **Channel** (e.g. Walmart): that single channel's full cost story — its waterfall, deduction breakdown, fine profile, dispute overhead, margin trend.

---

## 4. Time filter

- **Default:** FY2026 (current FY).
- **Options:** Full FY range (FY2024-FY2026) / FY2024 / FY2025 / FY2026 / quarters.
- **Combines with drill level** — e.g. "Walmart, FY2025" or "Distributors, Q3'25" are valid states.
- **Data-fidelity check:** the content's quarterly data runs Q1'25-Q1'26 (margin section). CONFIRM quarter granularity exists across *all* charts before exposing quarter filtering globally; if quarter data only exists for some charts, scope quarter-level filtering to where the data supports it rather than faking it.

---

## 5. Charts (D3, following the design system's chart rules)

**Chart inventory:**
- **Segment margin bars** (landing) — one per segment.
- **Waterfalls** (custom stacked-bar) — per-segment on landing; redrawn for a single channel on drill-down. The signature visual.
- **Revenue** — segment-grouped / all-channels view showing concentration (top 3 = 42%).
- **Trade deductions** — horizontal ranked bar, click-to-breakdown-by-type (preserve this existing interaction).
- **Compliance fines** — ranked bar, distinct accent (it's "the second invisible tax" — parallel structure to deductions).
- **Dispute overhead** — scatter/bubble (volume x cost) so Walmart reads as the outlier it is. Breaks the bar monotony.
- **Margin evolution** — multi-line slope chart by quarter, click-to-isolate a channel. (Lines for time-series only, per system.)

**Mandatory chart rules (from the design system):**
- Horizontal gridlines only (London-85). No vertical grid, no fills, no row shading.
- Reference/median lines: London-40, dashed, 2px.
- Every data point labeled.
- Compact axis formatting ($1.2M, 12%).
- Chart titles: Playfair, 22px, 700.
- Footnote required under every chart (11px italic).
- No gradients, no 3D, no rounded caps, no shadows. Horizontal bars preferred.
- **Palette:** centralize the official hardcoded hex arrays in `chartUtils.ts` (D3 can't read CSS vars — this matches the system's own approach). Use the categorical paired system (Chicago/HK/Tokyo/Singapore/Red, dark+light), sequential HK ramp for graded series, divergent HK-positive / London-85-neutral / Tokyo-negative where signed. Do NOT keep the current teal-only ramp as the sole palette.

---

## 6. Capital-allocation actions (the payoff)

Currently a numbered list buried at the bottom. Promote to the visual climax:
- **Dark callout cards** (`--ll-card-bg` #1a1a1a, white text) — the three actions (grow retail volume / restructure dispute triage / review Costco economics) as distinct cards.
- This is what the reader takes away; treat it as the destination, not a footnote.

---

## 7. Tables

- Keep the precise per-channel grids (existing `MarginTable` or a sortable grid) for the exact numbers in "the full picture" — tables are correct for precise per-channel data.
- Pair tables with the segment-comparison visual that lands the "distribution isn't actually cheaper" punchline.

---

## 8. Data fidelity (standing requirement — do not skip)

Interactivity means every chart computes **client-side from raw channel / deduction / dispute data** (the `computeMetrics`-style pattern) so filters and drill-downs recompute live.

- The client-side math **must reconcile to the canonical data pipeline numbers** — no drift between what the tool shows and what the source pipeline produces.
- **Source real COGS dollars from the dataset** to size the waterfalls. The current content gives COGS only as a *ratio* — the waterfall's largest step cannot be estimated; pull the actual dollar figure. If the figure isn't in the data, stop and flag rather than approximating.
- Verify a representative computed view (e.g. a single channel + single FY) against the pipeline output before considering the build done.
- Flag (unverified in CC's read): project notes mention `scripts/generate_json.py` as the data pipeline; confirm its presence and that the JSON under `src/data/` is its output before trusting it as source of truth.

---

## 9. Build hygiene

- Commit-gated; sensible logical commits (frame port / landing / drill model / each chart group / callouts).
- Build + deploy to Cloudflare; confirm live at channels.lailarallc.com matches main.
- Reuse existing components where they fit (`ChannelChart`, `TrendChart`, `CalloutCard`, `MarginTable`, `chartUtils.ts`) rather than rewriting; refactor them to the `--ll-*` token / official-palette standard.

---

## Open items flagged for resolution during build

1. **Quarter-data coverage** — confirm before exposing quarter filtering globally (section 4).
2. **COGS dollar figure** — source from data, do not estimate (section 8).
3. **`generate_json.py` pipeline** — confirm it exists and feeds `src/data/` (section 8).
4. **Astro frame pattern** — this is the first Astro consumer; document the port so it's reusable.

---

## Separate follow-up (not part of this build)

`LAILARA_DESIGN_SYSTEM.md` and `lailara-frame.css` disagree on some values (e.g. the spec says 900px body in places, frame says 1200/720). The doc is stale relative to decision D-001. Reconcile the markdown to match the frame so it stops misleading the next reader. Track separately; don't block this build on it.
