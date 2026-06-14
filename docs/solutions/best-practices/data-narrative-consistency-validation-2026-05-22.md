---
title: "Data-Narrative Consistency: Automated Validation for Hardcoded Prose Claims"
date: 2026-05-22
category: best-practices
module: data-pipeline
problem_type: best_practice
component: testing_framework
severity: medium
applies_when:
  - "Static sites embed numeric claims in MDX or markdown prose"
  - "Upstream data sources (Postgres, APIs) change independently of the published narrative"
  - "A generation script transforms raw data into JSON consumed by frontend components"
  - "Multiple channels, products, or entities each have distinct numeric claims in prose"
tags:
  - data-validation
  - prose-consistency
  - mdx-narrative
  - json-pipeline
  - regression-testing
  - upstream-refresh
---

# Data-Narrative Consistency: Automated Validation for Hardcoded Prose Claims

## Context

Static data-narrative sites (Astro + MDX, Next.js + MDX, etc.) embed numeric claims directly in prose: "DTC retains 83 cents of every dollar," "compliance fines total $872K," "Walmart margin is 80.3%." These claims are hardcoded strings, invisible to type checkers and linters, and silently become wrong when upstream data changes.

In this project (Cinderhaven channel profitability analysis), a 17x revenue scale-up in Postgres changed every channel's absolute dollar amounts and shifted relative rankings — distributors moved from middle-of-pack to best-margin channels, DTC dropped from 92 cents retained to 83. Without automated validation, 33 prose claims across 8 MDX files would have shipped incorrect numbers to readers.

The friction that prompted this guidance: upstream Postgres changes are made by data engineering with no awareness of the published narrative. The narrative authors have no automated signal that their prose is now wrong. Manual spot-checking doesn't scale past a handful of claims.

(session history) Prior sessions revealed this pattern after an initial data refresh broke inline claims silently — the test suite was built specifically to catch this class of drift.

## Guidance

Build three layers of defense:

### Layer 1: Validation test suite (`tests/test_prose_data.py`)

A standalone Python script (also runnable via pytest) that loads the generated JSON files, computes the same values the prose claims, and asserts they match within tolerance.

```python
def margin_pct(layers, channel_name):
    rev = layer_value(layers, 0, channel_name)
    net = layer_value(layers, 4, channel_name)
    return (net / rev) * 100

r.check("Walmart margin 80.3%", margin_pct(layers, "Walmart"), 80.3, tolerance=0.005)
r.check("Trade deductions $785K", trade_total, 785_000, tolerance=0.03)
r.check_range("Erosion range 17%-56%", min(all_erosion), max(all_erosion), 17, 56)
```

Key design choices:
- **Dual-mode execution**: runs standalone (`python tests/test_prose_data.py`) or via pytest, no external dependencies required
- **Tolerance-based checks**: `tolerance=0.005` for percentages, `0.01-0.03` for dollar amounts — avoids false failures from rounding
- **Range checks** for claims like "retailers retain 80 to 91 cents"
- **Schema validation** alongside prose checks — ensures JSON structure matches what TypeScript components expect
- **30+ checks** covering every numeric claim in every MDX file

### Layer 2: Generation script with snapshot fallback (`scripts/generate_json.py`)

The script embeds snapshot constants (last-known-good values from Postgres) and can also query Postgres live. This dual mode means:
- CI and local dev always work (snapshot mode, no DB required)
- Data refreshes pull live values and update the snapshots in the same commit

```python
FISCAL_REVENUE = {
    "Walmart": 10_894_584,
    "Kroger":   8_766_437,
    # ... all channels
}
```

### Layer 3: Single-command refresh workflow

```bash
python scripts/generate_json.py          # regenerate JSON from snapshots (or live DB)
python tests/test_prose_data.py          # validate prose still matches
# If failures: update MDX prose, re-run until clean
```

(session history) The refresh pipeline includes backup-before-write — the script preserves old JSON before overwriting, so a bad refresh can be rolled back without git gymnastics.

## Why This Matters

The 17x data scale-up exposed 33 broken prose claims in a single refresh. Without the validation suite, these would have shipped as published fact. The claims weren't just wrong in magnitude — they reversed the narrative's central conclusion (which channel type has the best margins).

Manual review cannot catch this reliably:
- Dollar amounts that shift from $41K to $785K are easy to spot; percentages that shift from 82.6% to 82.7% are not
- Range claims ("9% to 20%") require recomputing from multiple channels
- Cross-referencing 30+ claims across 8 files against 3 JSON files is tedious and error-prone

The validation suite runs in under a second and catches all of these.

(session history) Early iterations of this approach tried inline Python validation via PowerShell heredocs — this failed three times due to escaping issues. The standalone Python script approach was adopted after those failures.

## When to Apply

- Any static site that embeds numeric claims in prose (MDX, markdown, HTML templates)
- Projects where upstream data sources change independently of the published content
- Multi-channel or multi-entity analyses where each entity has distinct numeric claims
- Sites with a data generation pipeline that transforms raw data into frontend-consumable JSON
- Portfolio pieces or client deliverables where incorrect numbers damage credibility

Does NOT apply to:
- Fully dynamic sites where prose is generated from data at render time
- Projects where data is frozen and will never be refreshed
- Single-number dashboards where the number is always computed, never hardcoded

## Examples

### Before: silent drift

```
# 01-headline.mdx (stale)
DTC retains 92 cents of every dollar earned.

# channels.json (refreshed from Postgres)
DTC gross_revenue: 572510, net contribution: 472847
# Actual: 572510 * 0.826 ≠ 92 cents — it's 83 cents
```

No test catches this. The site ships with wrong numbers.

### After: automated catch

```
$ python tests/test_prose_data.py
=== Prose vs Data Validation ===

FAILURES:
  FAIL: DTC retains 92 cents — expected 92.00, got 82.60
  FAIL: Trade deductions $41K — expected 41000.00, got 785000.00
  ... 31 more failures

2 passed, 33 failed
```

Every broken claim is surfaced with expected vs actual values. The developer updates the MDX prose and re-runs until clean.

### Test structure pattern

Each MDX file section gets its own block of assertions:

```python
# --- 01-headline.mdx claims ---
r.check("DTC retains 83 cents", dtc_margin, 82.6, tolerance=0.01)

# --- 03-deductions.mdx claims ---
r.check("Trade deductions $785K", trade_total, 785_000, tolerance=0.03)

# --- 07-contribution.mdx claims ---
r.check("Walmart margin 80.3%", margin_pct(layers, "Walmart"), 80.3, tolerance=0.005)
```

## Related

- `tests/test_prose_data.py` — the validation suite (30+ checks)
- `scripts/generate_json.py` — data generation with snapshot constants
- DECISIONS.md — documents the dual-mode test design choice
- AUDIT.md issues #2-#3 — related data integrity concerns
