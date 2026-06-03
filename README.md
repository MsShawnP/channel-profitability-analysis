# Channel Profitability Analysis

Channel-by-channel profitability analysis for Cinderhaven, a fictional ~$25.6M/yr specialty food brand (3-year cumulative $76.8M). Examines contribution margins across 10 retail, distributor, and DTC channels through a five-layer cost waterfall (COGS, trade deductions, compliance fines, operational overhead) to inform capital allocation decisions.

Part of the Cinderhaven portfolio — first buyer-facing consumer of the Cinderhaven Data Platform.

**Live:** https://channels.lailarallc.com

## Stack

- **Framework:** Astro 5.9 (static site with React islands)
- **Charts:** D3 v7 + React 19
- **Content:** MDX narrative sections
- **Data pipeline:** Python script with embedded constants → JSON
- **Deployment:** Cloudflare Pages (via Wrangler)
- **Typography:** Self-hosted Playfair Display + Source Sans 3
- **Types:** TypeScript

## Setup

```bash
npm install
npm run dev        # dev server at localhost:4321
npm run build      # production build to dist/
npm run deploy     # build + deploy to Cloudflare Pages
```

## Data Pipeline

Data flows from a Postgres database on Fly.io through embedded Python constants to JSON files consumed by the Astro site:

```
Postgres (SSOT) → scripts/generate_json.py → src/data/*.json → MDX → React/D3
```

To refresh data from the database:

```bash
python scripts/refresh_data.py   # requires flyctl authenticated
```

To regenerate JSON from existing snapshot constants (no DB needed):

```bash
python scripts/generate_json.py
```

## Data contract

Canonical Cinderhaven conformance — 50 SKUs across 5 product lines and 6 contracted retailers.

## Validation

```bash
python tests/test_prose_data.py    # 34 checks: prose claims vs JSON data
python scripts/verify_math.py      # layer consistency + cross-file checks
python scripts/verify_roi.py       # dispute overhead breakdown
```

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
